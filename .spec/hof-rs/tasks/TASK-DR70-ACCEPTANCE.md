# TASK-DR70-ACCEPTANCE — independent acceptance of the D273 route-lifecycle batch

- Judge: a fresh acceptance subagent with no upstream conversation context. Nothing in
  `TASK-DR70-REPORT.md` was treated as evidence; every number below was produced by me.
- Object: outer repo `F:\moonbit-hof-rs`, `HEAD = ad0c56e420fbce83f4a7ee4b6c52b4871de10073`,
  batch range `a58bd72..HEAD` (7 commits: 6 `(DR-70)` commits + `ad0c56e` task book/report).
- Offline: no Godot, no external service, no network, no model endpoint, no real-machine round.
  Loopback sockets only (the same doubles the shipped tests use), plus read-only git/filesystem work.
  I wrote **zero bytes under `runs/**`** (verified by digest and mtime, §C8).
- I wrote nothing inside the repo except: the five controlled `src/**` plants in §6 (each restored
  byte-exactly) and this report. All analysis scripts, backups and probe crates live outside the repo in
  `C:\Users\wyl\AppData\Local\Temp\dr70acc\` (plus a read-only reuse of the implementer's backups at
  `C:\Users\wyl\AppData\Local\Temp\dr70\bak\`).
- **Verdict: `fail`** — narrow. All five task-book items are substantially delivered and independently
  reproduced; the fail is carried by one **moderate** new risk the batch introduced and did not disclose
  (a failed round-game start can leave a published route behind, and I observed that route inside the first
  role's window), plus three **minor** items (a corrected redaction note whose byte counts are themselves
  false, a residual `editor_play_scene` contradiction between the prompt and the skill that the new guard
  deliberately does not see, and no delivered test for a failing `start_round_game`). Details and the exact
  minimal fixes are in the defects table.

---

## 0. Structured verdict (machine-readable)

```json
{
  "verdict": "fail",
  "verdict_scope": "Fail is narrow and does not deny the batch: ① window containment, ② freshness/pid/reachability validation, ④ harness wiring coverage and ⑤ byte-exact evidence restoration are each independently reproduced as real and load-bearing (my plants MY-P1/2/3/4/5 redden exactly their target tests and restored byte-exactly). The fail rests on (a) MODERATE: a round-game start that fails after the adapter already published its record leaves that route on disk, and my run-level probe observed it inside the first role window, so an empty/fresh project can still expose a route the start could not confirm; the report does not mention this new risk; (b) MINOR: the DR-70 correction box in REDACTION.md and report section 3.5 state byte counts that are false (54/30 and 25/30) while the true values are 52/28 and 23/28 (net deltas -24 and +5 are correct); (c) MINOR: developer.md still orders the Developer to call editor_play_scene while the delivered skill forbids it, and e1_increment.rs:780 enforces the prompt side; the new audience-aware guard does not test developer.md for that command; (d) MINOR: no delivered test drives a failing start_round_game, so the non-fatality is code-only in the shipped suite. The publish/adopt path is also not presence-atomic and is untested under a race (my probe saw the route absent in 4759 of 8227 concurrent reads), but the loss mode is an explicit refusal, not a transport error.",
  "criteria": [
    {"id": "C1-window-containment", "pass": true, "evidence": "run_loop.rs:718 starts the round game before the first role; run() at :571-580 tears it down on every exit path. tests/round_game_window.rs spawns the real hoh binary (CARGO_BIN_EXE_hoh, HOH_GAME_ROUTE) inside the Developer and Tester steps of a real run_loop::run, asserts RouteProbe.route_exists true, exit Some(0), and that the loopback game double received exactly two running_game_get_scene_tree calls while the editor received none. Green at HEAD: 3 passed / 0 failed (my run). Scope caveat: the game endpoint and the adapter start are doubles, so the engine-level claim is structural, not observed."},
    {"id": "C1-plant-window", "pass": true, "evidence": "My own plant MY-P1 (delete the start_round_game call at run_loop.rs:718) makes round_game_window RED: the_published_route_covers_the_developer_and_tester_windows panicked at tests/round_game_window.rs:270 with RoleProbe { route_exists: false, exit_code: Some(5), stderr: hoh: game_endpoint_unavailable ... Falling back to the editor endpoint is not allowed (DR-43) } — the exact DR-69 D1 symptom. a_failing_round_still_withdraws_the_published_route also RED. Restored: byte == my backup, hash-object d2e1d3d8276d5bab008ca757987d83da46826227 == HEAD blob, status empty, diff --stat empty."},
    {"id": "C2-fresh-project-graceful", "pass": true, "evidence": "External probe drives the REAL GodotAdapter::start_round_game (no repo edits) with a loopback editor double. Case A (editor refuses to play a project with no main scene): start_round_game -> Err 'editor_play_scene: JSON-RPC error -32000: no main scene is configured; nothing to play', and route.exists() == false. A full run_loop::run with an adapter whose start_round_game always fails still reaches its first role (harness invocations 1) and records a warning in runs/run-1/warnings.log: 'DR-70: the round's game session could not be started (...); the game route stays withdrawn until the battery starts its own game'. So the round does NOT fail and nothing is published when the editor cannot play."},
    {"id": "C2-fresh-project-route-that-lies", "pass": false, "evidence": "The real GodotAdapter publishes at godot.rs:3853 (register_game_endpoint) BEFORE the readiness poll at :3856-3876, and bails at :3871 without withdrawing. Probe case B (editor announces an endpoint on a closed loopback port, live pid): start_round_game -> Err, yet route exists: true with bytes {endpoint ... pid alive}. Run-level probe (adapter publishes then fails): the route is visible inside the FIRST ROLE's window (Some(true)) and is only withdrawn at round teardown. Adoption refuses the closed-port form (use_game_route_file -> None) but ACCEPTS the answering-port form (probe case C, adoption returned Some(record)), so a game that answers but is not ready yields a published route that is adopted. This violates the stated requirement that a fresh project must not turn 'no scene yet' into a route that lies."},
    {"id": "C3-stale-vice-live", "pass": true, "evidence": "game_route_across_processes.rs at HEAD: 6 passed / 0 failed (my run). Closed port -> explicit refusal (asserts no 'MCP transport failure' and no '10061'); dead pid with a live answering port -> explicit refusal and the live endpoint receives nothing; expired record -> explicit refusal; live route -> real subprocess exit 0 with the game double receiving the call. My plant MY-P2 removes only the pid-liveness block in endpoint.rs validate_published_route: a_route_whose_recorded_game_process_is_gone_is_refused_even_when_the_port_answers goes RED (assertion left != right failed: left Some(0) right Some(0)) — the liveness check is load-bearing. Restored byte-exactly (endpoint.rs blob e805a421b269f454482b4d957f43c3e7af5b6f76)."},
    {"id": "C4-round-teardown", "pass": true, "evidence": "run() (run_loop.rs:571-580) calls stop_round_game unconditionally after run_inner, and stop_round_game itself also calls withdraw_game_route directly (belt and braces, :559-561); run_inner withdraws any inherited file at :600 before use_game_route_file. a_failing_round_still_withdraws_the_published_route (Err from the contract gate before the battery) asserts the route existed during the Developer window and route.exists() == false afterwards; a_route_left_by_another_round_is_not_inherited plants a fully valid leftover (live port, live pid, fresh) and asserts a role sees route_exists false and the decoy game receives nothing. My plant MY-P5 deletes the wrapper teardown: both tests RED (round_game_window.rs:311 stub.stops() >= 2 and :375 error-path teardown). Restored byte-exactly."},
    {"id": "C5-three-sites-and-guard", "pass": true, "evidence": "developer.md:31-40 no longer names a concrete running_game_<tool> and states the round-wide route plus 'before your edits'; godot-dev.md:65-90 gives only editor-side self-tests (editor_get_errors / editor_get_output_log / project_read_script), states 'before you changed the code', and forbids tools call editor_play_scene; developer_contract.rs:118-134 swapped the running_game_get_node_property_samples needle for editor_get_errors + 'before you changed the code' (one concrete tool left, two concrete requirements entered). delivered_materials at HEAD: 5 passed / 0 failed. My plant MY-P3 reinstates the exact old running_game_get_node_property_samples recipe in godot-dev.md: no_developer_facing_material_sends_the_role_to_the_game_process RED with the message naming running_game_get_node_property_samples; the other four tests stay green. Restored byte-exactly (godot-dev.md blob 578cce712ec175770f7d1677d26bce360a532198)."},
    {"id": "C6-wiring-coverage", "pass": true, "evidence": "harness_cap_wiring.rs::the_harness_itself_bounds_what_the_next_request_carries drives the real MiniHarness::invoke against a loopback chat endpoint and inspects the raw body of the request that follows a 2 MiB tool result. My plant MY-P4 deletes the CappedEnvironment wrapper at src/harness/mini.rs:66-69: this test goes RED with 'the request that follows the 2 MiB tool result must not carry it: 2097786 bytes were sent' (0 passed / 1 failed). Restored byte-exactly (mini.rs blob 85b0eef0bf472000b152997db0f41cc18464a13c). The DR-69 D4 hole (suite green with the wrapper deleted) is closed."},
    {"id": "C7-evidence-restoration", "pass": true, "evidence": "Byte comparison against git history dc9d350 (== 3adab37^): ORIGINAL bytes 52200 / CR 0 / LF 184 / records 184 / sha256 a362c02a...ab7e; WORKTREE bytes 52205 / CR 0 / LF 184 / records 184 / sha256 141fda10...752c. Common prefix 2736, common suffix 49441; original replaced run b'$(cat /c/Users/wyl/AppD' (23 bytes) -> b'<redacted-key-path-by-DR-69>' (28 bytes); everything else identical: True; single_substitution: True; dir /b -p count 1 == 1; worktree hash-object 763a3a3e4f847efadc820efbf584461ced591c17 == HEAD blob. git check-attr text -> 'text: unset' (the .gitattributes pin is active) with core.autocrlf=true. Credential scan: the 51-char value from config/model.secret.env appears in 0 of 6819 tracked files."},
    {"id": "C8-gates-and-guards", "pass": true, "evidence": "Fresh external target dir, CARGO_INCREMENTAL=0, from scratch: cargo test --offline --no-fail-fast -> 50 test-result lines, 455 passed / 0 failed / 7 ignored, CARGO_EXIT=0 (matches the report exactly; >= 436/0/7 and ignored did not grow). cargo fmt --check -> exit 0. Test functions a58bd72 -> HEAD: 443 -> 462, REMOVED = []; tests/godot_smoke.rs #[ignore occurrences 8 == 8; git ls-files '*.rs' = 87. Implementer plants P1..P5 are byte-identical to their own pre-plant backups under %TEMP%\\dr70\\bak with hash-object == HEAD blob (85b0eef0bf / 7831f3593f / d2e1d3d827 / 578cce712e). My five plants restored byte-exactly with empty git status --porcelain -uall, empty git diff --stat, and empty git diff --cached --stat. runs/smoke-t6|t7|t8|t9 digests (scheme in section 4) unchanged, newest mtimes 09/29 02:32:01, 09/29 14:41:14, 09/30 07:58:28, 09/30 11:27:29; zero files/dirs newer than 2026-09-30 11:27:30 in any of the four trees. .workspace/mario live artifact tree (17 files, excluding .hoh/.git/.godot/.import) byte-identical to runs/smoke-t9/versions/1f3d20ed... and to iter-1/planner-view. PRD-mario.md sha256 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a. git diff --numstat a58bd72..HEAD for DECISIONS.md, .workspace/mario, PRD-mario.md, godot-mcp and for Cargo.toml/Cargo.lock all empty. origin/master 9aebbe15f13508d1ee5063505b2827ee59cc041a, ahead 18, nothing staged or pushed. Nested engine git -C godot-mcp/godot HEAD fc63af77c33368c4a1bb839c95d19750554f63a3, status --porcelain -uall 0 lines; outer pathspec really matches (ls-files godot-mcp = 6484 vs ls-files godot-mcp/godot = 0). All three false-green traps reproduced (section 5)."},
    {"id": "C9-concurrency-and-honesty", "pass": true, "evidence": "Concurrency: publish_game_route is write-temp + remove + rename; my race probe (one publisher thread, one reader thread, same path, 1.5 s) observed 8227 reads of which 4759 (57.85%) saw NO route, and 0 corrupt/torn reads. So content is atomic (temp+rename) but presence is not, and nothing in the batch tests or synchronises this; the loss mode is an explicit game_endpoint_unavailable, not a transport error. Honesty: the report explicitly declines to state any real-machine success probability (section 6.1-2: I cannot disprove it offline and give no probability), states it does not claim E1 or E3 met (section 7.1), and states the routing problem is not fully solved (section 7.7). I agree with every one of those three."}
  ],
  "defects": [
    {"id": "A1", "severity": "moderate", "what": "A round-game start that fails AFTER the adapter published its record leaves the route on disk; the runtime does not withdraw it at that point, so a fresh/empty project can expose a route the start could not confirm. The real GodotAdapter publishes at godot.rs:3853 and only then polls readiness at :3856; when the poll fails it bails at :3871, and run_loop.rs start_round_game (:526-545) only appends a warning. My run-level probe observed the route existing inside the first role window (Some(true)). This directly contradicts the stated requirement that 'no scene yet' must not become a route that lies. The ② checks mitigate the common forms (closed port or dead pid -> explicit refusal), but an answering port with a live pid is ADOPTED (probe case C), and the report never mentions this new risk.", "reproduction": "External crate C:\\Users\\wyl\\AppData\\Local\\Temp\\dr70acc\\probe: tests/round_game_start.rs (case B route exists true after a failed start; case C adopted Some(record)) and tests/round_start_failure.rs (route visible during the first role: Some(true)); source: src/adapter/godot.rs:3849-3876 and src/runtime/run_loop.rs:526-545, 718. Fix: withdraw the route in the failure path of start_round_game (or in run_loop's wrapper) whenever the adapter's start returns Err."},
    {"id": "A2", "severity": "minor", "what": "The DR-70 correction is present and the old wording is preserved verbatim under a marked 'Superseded DR-69 text' heading, but its byte arithmetic is false: REDACTION.md line 13 says 'replacing 54 bytes with a 30-byte marker' and lines 31-32 say the truncated value '$(cat /c/Users/wyl/AppD' is 25 bytes and the marker is 30 bytes; TASK-DR70-REPORT.md section 3.5 repeats 25 and 30. The true values are 52 bytes replaced by 28 for DR-69, and 23 bytes replaced by 28 for DR-70. The net deltas (-24 and +5) and every structural fact (records 184/183/184, LF/CR, dir /b -p) are correct. This is the same defect class (self-report vs byte fact) that made DR-69 fail, recurring inside the correction itself.", "reproduction": "python C:\\Users\\wyl\\AppData\\Local\\Temp\\dr70acc\\dr69_redaction.py -> 'orig removed run (52 bytes)' and 'dr69 inserted run (28 bytes)'; python ...\\evidence_check.py -> common_prefix 2736, common_suffix 49441, len(orig run)=23, len(cur run)=28."},
    {"id": "A3", "severity": "minor", "what": "The three Developer-facing sites agree on the game-process contradiction but disagree about editor_play_scene: developer.md section [self-test] (line 109) and [definition-of-done] #3 (line 139) still order the Developer to boot the scene, while godot-dev.md section 5 (lines 88-90) says 'Do not start a game of your own (editor_play_scene): the runtime owns the round's session'. tests/e1_increment.rs:780 requires the prompt to contain editor_play_scene, and the new delivered_materials guard is audience-aware: it asserts only that the SKILL must not contain 'tools call editor_play_scene', and never checks developer.md for the same command. The report discloses the e1_increment constraint (section 6.1-3) but not that the guard leaves the prompt free to contradict the skill.", "reproduction": "sed -n '104,114p;137,140p' src/prompts/developer.md; sed -n '85,91p' src/prompts/skills/godot-dev.md; sed -n '780p' tests/e1_increment.rs; sed -n '109,126p' tests/delivered_materials.rs."},
    {"id": "A4", "severity": "minor", "what": "No delivered test drives a FAILING start_round_game. The scripted adapter only ever answers Ok(None) (no round_game configured) or Ok(Some(record)); the failure path that now sits before the first role of every round has no test in tests/**, so 'must not fail the round' is guaranteed by code inspection only in the shipped suite. (I closed that gap externally with the probe crate, which is how C2 was answered.)", "reproduction": "grep -rn 'start_round_game' tests/ -> tests/common/mod.rs:547-566 only (both arms are Ok); tests/round_game_window.rs uses Ok(Some) via with_round_game and Ok(None) via FakeAdapter::new()."},
    {"id": "A5", "severity": "minor", "what": "register_game_endpoint ignores a publish failure (src/tools/mod.rs:401-403: let _ = endpoint::publish_game_route(...)), while src/adapter/godot.rs:3850-3852 comments claim 'A registration failure is fatal here: a round whose game runs but whose route is not published is exactly the DR-69 defect'. Because publish errors never surface, a failed publish is silent: the round believes the route is published while every role still gets game_endpoint_unavailable. Inherited from DR-69, but it is load-bearing for this batch's headline claim.", "reproduction": "sed -n '395,405p' src/tools/mod.rs; sed -n '3849,3854p' src/adapter/godot.rs."}
  ],
  "risks": [
    "R1 (highest) The engine-level half of the headline is unverified: nothing offline shows that a real Godot accepts editor_play_scene before the Developer has written any code, that the round-wide game process survives the Developer's project_edit_script writes/reloads, or that an engine refuses a second play while one is running. The containment proof is real at the orchestration/channel level (real run_loop, real hoh subprocess, real route file) but structural at the engine level (loopback game double + FakeAdapter). Any claim that a real round now reaches the game endpoint is an inference.",
    "R2 The fresh-project window in defect A1 is the concrete form of R1 plus a design gap: if a real empty project makes editor_play_scene succeed but the game not answer, the round publishes a route it cannot confirm and leaves it until the next phase boundary or round end.",
    "R3 The publish/adopt path is not presence-atomic and is untested under a race (C9: 4759/8227 reads saw no route). In the real system the harness is the only publisher and publishes only a few times per round, so the practical probability is small, but nothing synchronises it and the loss mode is a spurious explicit refusal.",
    "R4 A route file remains a role-writable trust boundary (DR-69 R4): validate_published_route explicitly does not establish that the endpoint is THIS round's game. Any judge that treats role-CLI output as game observation should not rely on the route file.",
    "R5 The report's section 1.2 heading ('一次跑通...角色真能到达游戏端点') is stronger than its evidence: the role shell does reach the endpoint, but the endpoint is a double and the adapter is a double. Section 7.7 qualifies it correctly; a reader who stops at section 1.2 could over-read it.",
    "R6 The 6-hour expiry is the weakest ② check (a legitimate long round must not expire) and pid reuse on Windows is indistinguishable from liveness; the design leans on the reachability probe, which is itself inconclusive for any non-ConnectionRefused error.",
    "R7 Another residual from DR-69 survives: the key file path literal (keyval.txt) remains in TASK-SMOKE-T9-ACCEPTANCE.md, TASK-SMOKE-T9-REPORT.md (and now TASK-DR69-ACCEPTANCE.md, src/runtime/secrets.rs as fake fixtures). D272 adjudicated retention; the DR-70 report does not re-disclose it. No credential value remains anywhere (0/6819)."
  ],
  "unverified": [
    "U1 Real-machine behaviour of every kind: no Godot, no engine, no external service, no model endpoint, no real round. Everything about the engine belongs to inference.",
    "U2 I did not re-run the implementer's own plant red-outputs (their plants-output/gate logs). I byte-verified all five restores against their own backups and independently reproduced equivalent mechanisms with my own five plants, but their failure transcripts are their evidence, not mine.",
    "U3 The remainder of .spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/** was not byte-audited: I checked dev1_commands.txt, REDACTION.md and the .gitattributes pin.",
    "U4 I did not verify the report's historical narrative (DR-65..DR-69 old accounts) or the exact DR69-DR70 commit-by-commit mapping beyond the diffstat.",
    "U5 I did not exhaustively prove that CappedEnvironment is the only path by which an unbounded string can reach the next request (the DR-69 U8 boundary stands).",
    "U6 I did not test a panic in the runtime between the round-game start and run()'s wrapper: the wrapper withdraws on Err and on the summary path, but a panic would skip it.",
    "U7 The concurrency judgement is a probe-level observation (one publisher, one reader), not a formal analysis of the real multi-process adopt/publish interleavings.",
    "U8 I did not run the full suite on a clean checkout with a different cargo version, nor on a different OS (the Windows-only pid FFI path is what I exercised; the Unix kill(pid,0) branch is unexercised here)."
  ]
}
```

---

## 1. Per-item table (the nine jobs)

| # | Job | Verdict | My key evidence (self-produced) |
|---|---|---|---|
| 1 | Window containment + counterexample | **pass** (orchestration), engine unverified | `round_game_window` 3/3 green at HEAD; MY-P1 revert => RED with `route_exists: false` / exit 5 / DR-43 text; 2 real `running_game_get_scene_tree` hits on the game double, 0 on the editor |
| 2 | Fresh-project risk | **fail (partial)** | probe case A: editor refuses => no route + round still reaches role 1 + warning; probe case B + run-level probe: publish-then-fail leaves the route **visible during the first role**; case C: such a route is adopted |
| 3 | Stale vs live | **pass** | `game_route_across_processes` 6/6; closed port / dead pid / expired all explicit refusals; live route exit 0; MY-P2 => RED on the pid test |
| 4 | Round teardown incl. error paths | **pass** | `run()` wrapper :571-580 + belt-and-braces withdraw :559-561 + not-inherited :600; error-path test green; MY-P5 => 2 RED |
| 5 | Three sites + new guard | **pass for the targeted contradiction; minor residual** | developer_contract needle swapped; `delivered_materials` 5/5; MY-P3 => RED; A3: developer.md vs skill on `editor_play_scene` |
| 6 | Wiring coverage | **pass** | MY-P4 deletes the wrapper => `harness_cap_wiring` RED with 2,097,786 bytes; green at HEAD |
| 7 | Evidence restoration | **pass on bytes; minor note defect** | 52200->52205, CR 0, LF 184, records 184, single 23->28 substitution, blob 763a3a3e == HEAD; credential 0/6819; A2 wrong byte counts in the correction |
| 8 | Gates, plants, guards | **pass** | 455/0/7 EXIT=0; fmt 0; 443->462 tests, no removals; 5 implementer plants byte-identical to backups; my 5 plants restored byte-exactly; runs digests unchanged; all three traps reproduced |
| 9 | Concurrency and honesty | **judged: safe-but-untested race + honest report** | race probe 4759/8227 misses, 0 corrupt; report declines a real-machine probability, does not claim E1/E3 met, does not claim full resolution |

---

## 2. What I reproduced for the headline (job 1)

The publish window is opened by `run_loop.rs:718` (`start_round_game`, before the Planner) and closed by the
`run()` wrapper (`:571-580`) on every exit path, with additional stop/start at the battery boundaries
(`:1187`, `:1229`, `:1281`, `:1308`) so the round session and the battery's own `editor_play_scene` never
overlap. `start_round_game` in `GodotAdapter` (`godot.rs:3839-3878`) calls `editor_play_scene`, parses the
record, **registers (publishes)** and then polls readiness; `stop_round_game` (`:3886-3892`) stops the scene
and clears the endpoint.

`tests/round_game_window.rs` drives the **real** `run_loop::run` and, inside the Developer and Tester scripted
steps, spawns the **real** `hoh` binary with `HOH_GAME_ROUTE`. At HEAD it is green (3 passed / 0 failed, my
run): `route_exists: true` in both steps, exit `Some(0)`, the game double served exactly two
`running_game_get_scene_tree` calls, the editor served no `running_game_*`.

**My counterexample** (MY-P1) removes the single `start_round_game(...)` line at `:718` and the same test goes
red with the DR-43 refusal the real role would have received in DR-69. So the containment assertion genuinely
loads on the change, and the role side is a real subprocess reading the real published file — not a stub.

**Judgement on "real or merely structural in a double":** the *window containment* is real (orchestration,
phase order, file publication and cross-process adoption are all production code, and the role shell is a real
process). The *game* is a double and the adapter start is a double, so "the game is alive and playable for the
whole role window" remains structural. The engine-level facts (does a real editor accept a round-wide
`editor_play_scene` before any code exists; does the game survive the Developer's edits) are unverified
offline and must be answered by a real round.

---

## 3. The fresh-project risk (job 2) — the one I was asked to judge

I built an external crate (`%TEMP%\dr70acc\probe`) that depends on `hof-rs` by path and drives the **real
production** `GodotAdapter::start_round_game` against a loopback editor double — no Godot, no repo edits.

* **Case A — the editor refuses to play (no main scene / nothing to play).** `editor_play_scene` returns a
  JSON-RPC error; `start_round_game` returns `Err` at `godot.rs:3848`, i.e. **before** parsing or publishing.
  Observed: `route exists: false`. A full `run_loop::run` with an adapter whose `start_round_game` always
  fails still invokes its first role (harness invocations = 1) and writes the warning
  `DR-70: the round's game session could not be started (…); the game route stays withdrawn until the battery
  starts its own game`. **No route, no round failure — graceful.**
* **Case B — the editor announces an endpoint but the game never answers the readiness poll.** The record is
  **already published at `godot.rs:3853`**, the poll fails, and the function bails at `:3871` without
  withdrawing. Observed: `start_round_game -> Err`, and `route exists: true` naming a closed port with a live
  pid. My run-level probe confirms this route is **visible while the first role runs** (`Some(true)`), and is
  withdrawn only at round teardown.
* **Adoption of that leftover.** A closed-port route is refused (`use_game_route_file -> None`), which keeps
  A1 from becoming a transport error — but a route whose port answers and whose pid is alive is **adopted**
  (probe case C returned `Some(record)`), so a game that is up but not ready can still be reached.

**Judgement:** the requirements "must degrade gracefully" and "must not fail the round" hold and I verified
them. The requirement "must not turn 'no scene yet' into a route that lies" **does not hold** in the
publish-then-fail path: the route outlives the failed start into the role window. This is a new risk created
by moving the start earlier, and `TASK-DR70-REPORT.md` never mentions it.

---

## 4. Digest scheme, self-validation, and guard raw output

Digest scheme (identical to the DR-69 acceptance and the DR-70 report, so values are comparable): Windows
PowerShell 5.1 (`5.1.26100.6584`, culture `zh-CN`), `Get-ChildItem -Recurse -Force -File`; per file the
repo-root-relative **lowercased POSIX** path + byte length + lowercased SHA256, tab-joined, `\n`-joined, whole
string UTF-8 hashed with SHA256; line order by `Sort-Object` (culture sort).

```
runs/smoke-t6 files=135 hash=c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03 newest=09/29/2026 02:32:01
runs/smoke-t7 files=115 hash=6e4c1595753c2cdefb16e4d2e5f05242ca202c70c81a93e98ae2b9c92b520fb7 newest=09/29/2026 14:41:14
runs/smoke-t8 files=358 hash=6d11b2c61ec507b5f02525ddc0e7f7adb08763cd2439a4b08788b7fe51bdf5a7 newest=09/30/2026 07:58:28
runs/smoke-t9 files=83  hash=541e2d814e563ba667c95bde49765d05e44cf11aa5ab90b2f44931f30136ca9d newest=09/30/2026 11:27:29
```

**Self-validation:** `runs/smoke-t6 = c144ef32…7a9c03` hits the required value, and t7/t8/t9 match every prior
record — so the scheme is the same one and the four trees are byte-unchanged. **Write-then-delete check:**
files and directories with `LastWriteTime > 2026-09-30 11:27:30` are `0/0` in all four trees (I re-ran this
after the full gate and after all plants). `runs/**` received nothing from me.

Guards:

```
PRD-mario.md sha256 = 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a
git diff --numstat a58bd72..HEAD -- DECISIONS.md .workspace/mario PRD-mario.md godot-mcp  -> empty
git diff --numstat a58bd72..HEAD -- Cargo.toml Cargo.lock                                -> empty
origin/master = 9aebbe15f13508d1ee5063505b2827ee59cc041a ; git rev-list --count origin..HEAD = 18
git diff --cached --stat -> empty ; git status --porcelain -uall -> empty
nested: git -C godot-mcp/godot rev-parse HEAD = fc63af77c33368c4a1bb839c95d19750554f63a3 ; status -uall = 0 lines
outer pathspec control: ls-files godot-mcp = 6484 vs ls-files godot-mcp/godot = 0
live .workspace/mario artifact tree (17 files) == runs/smoke-t9/versions/1f3d20ed… == iter-1/planner-view (bytes)
.gitattributes: .spec/hof-rs/tasks/TASK-SMOKE-T9-evidence/** -text ; git check-attr text -> unset
```

---

## 5. The three false-green traps (reproduced)

1. **A nonexistent pathspec says nothing.** `git diff --stat -- definitely/not/a/real/path` -> empty output,
   `exit 0`. Reading: an empty diff proves nothing until the pathspec is shown to match. Control:
   `ls-files godot-mcp = 6484` vs `ls-files godot-mcp/godot = 0`.
2. **cmd eats `^` and expands `%errorlevel%` at parse time.** Bash: `git cat-file -e
   dc9d350:.spec/hof-rs/REQUIREMENTS.md` -> exit 0; `...:definitely/not/here` -> exit 128. cmd:
   `git rev-parse dc9d350^` printed `dc9d350dff7357fec88d532ed5d2661a6ce7de18` (the `^` never reached git),
   and an `&`-chain printed `%errorlevel%=0` for a command that had just fataled. Reading: only bash has
   evidential force here.
3. **The outer repo does not track the engine tree, the workspace or the run dirs.**
   `git check-ignore -v runs/smoke-t9/meta.json` -> `.gitignore:12:runs/`; `.workspace/mario/project.godot` ->
   `.gitignore:11:.workspace/`; `godot-mcp/godot` -> `.gitignore:33:godot-mcp/godot/`; and
   `git diff --stat -- godot-mcp/godot/bin` -> empty + `exit 0`. Reading: an empty diff over an ignored path
   proves nothing; that is why the nested-repo HEAD/status and the live-vs-snapshot byte comparison exist.

---

## 6. My plants and counterexamples (all production code, all restored byte-exactly)

Driver: `python %TEMP%\dr70acc\myplants.py apply|restore|verify <id>` (my own byte anchors, my own out-of-repo
backups in `%TEMP%\dr70acc\myplants`).

| Plant | File (production) | Mechanism disabled | Result | Restore evidence |
|---|---|---|---|---|
| **MY-P1-window** | `src/runtime/run_loop.rs` | delete `start_round_game(...)` at `:718` | `round_game_window` **2 RED** (`:270` `route_exists: false`, exit 5, DR-43 text; plus the error-path test) | byte == my backup; hash-object `d2e1d3d827…` == HEAD; status/diff empty |
| **MY-P2-pid** | `src/tools/endpoint.rs` | drop the `process_is_alive` block in `validate_published_route` | `game_route_across_processes` **1 RED** — `a_route_whose_recorded_game_process_is_gone…`, `left Some(0) right Some(0)` | byte == my backup; `e805a421b269…` == HEAD; status/diff empty |
| **MY-P3-text** | `src/prompts/skills/godot-dev.md` | put `running_game_get_node_property_samples` back | `delivered_materials` **1 RED** (`no_developer_facing_material…` names the tool) | byte == my backup; `578cce712e…` == HEAD; status/diff empty |
| **MY-P4-cap** | `src/harness/mini.rs` | delete the `CappedEnvironment` wrapper | `harness_cap_wiring` **1 RED**: `must not carry it: 2097786 bytes were sent` | byte == my backup; `85b0eef0bf…` == HEAD; status/diff empty |
| **MY-P5-teardown** | `src/runtime/run_loop.rs` | delete the wrapper's `stop_round_game` | `round_game_window` **2 RED** (`:311` `stub.stops() >= 2`; `:375` error-path teardown) | byte == my backup; `d2e1d3d827…` == HEAD; status/diff empty |

Non-mutating counterexamples (external crate, no repo edit):

* **Probe case B / case C / run-level** — §3 above; the failed-start route survives into the role window and
  a port that answers is adopted.
* **Race probe** — `publish_race.rs`: 8227 reads, 4759 misses (57.85%), 0 corrupt.

Implementer plants (P1..P5): I confirmed each of the five targets is **byte-identical to the implementer's own
pre-plant backup** under `%TEMP%\dr70\bak`, with `git hash-object == HEAD:<path>` (`85b0eef0bf`,
`7831f3593f`, `d2e1d3d827`, `578cce712e`). I did not re-run their red transcripts (U2). All five plants live
under `src/**` (godot-dev.md is `include_str!`-embedded production material).

---

## 7. Evidence repair, byte for byte (job 7)

```
ORIGINAL dc9d350 : bytes 52200  cr 0  lf 184  records 184  sha256 a362c02a…ab7e
WORKTREE         : bytes 52205  cr 0  lf 184  records 184  sha256 141fda10…752c
common_prefix 2736  common_suffix 49441
orig replaced b'$(cat /c/Users/wyl/AppD'      (23 bytes)
cur  replaced b'<redacted-key-path-by-DR-69>' (28 bytes)
single_substitution True   everything_else_identical True
'dir /b -p' count 1 == 1   HOH_MODEL_API_KEY count 1 == 1
worktree git hash-object  763a3a3e4f847efadc820efbf584461ced591c17
HEAD blob                 763a3a3e4f847efadc820efbf584461ced591c17
```

The record boundary, the line endings and the `dir /b -p` evidence are back and the credential channel is
gone; the only edit is the 23->28 byte substitution, matching the DR-70 report's own arithmetic except for its
stated component sizes (defect A2). `config/model.secret.env`'s 51-character value appears in **0 of 6819
tracked files**. `keyval.txt` appears in 4 tracked files (2 T9 reports, the DR-69 acceptance report and a fake
fixture in `src/runtime/secrets.rs`) — the D272-adjudicated residual, now also re-listed in R7.

---

## 8. What I did not check

* Any real-machine behaviour (U1), including whether the engine accepts a round-wide play/stop sequence.
* The implementer's own failure transcripts for P1..P5 (U2) — I checked their restores byte-for-byte.
* The rest of `TASK-SMOKE-T9-evidence/**` beyond the command dump, `REDACTION.md` and the `.gitattributes`
  pin (U3); the batch's historical narrative and pre-DR-70 git archaeology (U4).
* Whether `CappedEnvironment` is the only unbounded path into the next request (U5); panic-path teardown
  (U6); a formal multi-process race analysis (U7); non-Windows pid liveness (U8).
* I did not re-verify the whole suite on a clean checkout of `a58bd72` (I measured the delta by parsing test
  functions and by the reported baseline, not by re-running the base).

---

## 9. Advice for the next batch

1. **Withdraw the route when the round-game start fails** (A1). The smallest correct fix is in the runtime's
   `start_round_game` wrapper: on `Err`, call `withdraw_game_route(game_route_path(run_dir))` in addition to
   the warning — that removes case B regardless of what the adapter published before failing. Add the missing
   delivering test (A4): an adapter whose `start_round_game` returns `Err` must (i) still reach the first role
   and (ii) leave no route file.
2. **Correct the correction** (A2): REDACTION.md and report §3.5 must say 52/28 and 23/28 (the net deltas stay
   -24/+5). The evidence bytes are fine; only the prose numbers are wrong.
3. **Resolve the `editor_play_scene` contradiction** (A3): either drop it from `developer.md`'s `[self-test]`
   and definition-of-done #3 (and update `e1_increment.rs:780` accordingly), or explicitly scope the skill's
   ban to "do not boot a second game while the round session is live" and extend `delivered_materials` so it
   checks the prompt for the same command.
4. **Make publication presence-atomic** if cheap (write the temp next to the target and use a
   replace-on-rename that does not require a `remove_file` first, or retry a `None` read once), and surface
   publish errors instead of `let _ =` (A5) so "the route is published" is not silently false.
5. **Do not treat the containment test as engine evidence.** The real-machine round should first record, in
   its own words, what `editor_play_scene` does on an empty project and whether the round-wide session
   survives the Developer's writes; that is the one thing no offline batch can settle (R1/R2). Until then, do
   not claim E1/E3 met and do not reuse an observability plan pinned on `running_game_*`.

---

## 10. One line

**All five named fixes are real and I reproduced each one — with my own five production plants reddening the
exact target tests and restoring byte-exactly, a clean 455/0/7 gate, fmt clean, four `runs/**` trees and the
mario tree byte-unchanged, and the frozen evidence restored to a single 23->28 byte substitution — but the
batch is `fail` because moving the game start before the first role introduced a route-lifetime hole it does
not withdraw on a failed start (observed inside the first role window, moderate, undisclosed), the corrected
redaction note states false byte counts, developer.md and the delivered skill still contradict each other on
`editor_play_scene`, and the publish/adopt path is presence-racy and untested.**
