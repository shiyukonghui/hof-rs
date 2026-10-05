{
 "verdict": "pass_with_defects",
 "task": "independent acceptance of the bevy round 3/4 evidence, the nine-step battery, the artifact gate, the economics, PRD coverage, the tree gate and the forbidden zones",
 "revision_measured": "branch bevy-core, HEAD f7e87ee (clean: `git status --porcelain` empty, `git diff HEAD` empty)",
 "measured_at": "2026-10-05, offline; no engine, no game, no network, no round run; no write under runs/**",
 "environment": "helper scripts and logs under F:/hof-acc-work and F:/hof-acc-logs; build directory F:/hof-acc-target (my own); no tracked file modified by me",
 "criteria": [
  {
   "id": "C1-round4-identity-attributable",
   "pass": true,
   "evidence": "runs/bevy-round4/launch.json identity: spawned_pid=answering_pid=listening_pid=47624, nonce=faf2adda-c698-48ef-a4f5-f51d1da551c6, verified=true, stop.pid_dead=true, client_generation=1. The nonce is byte-equal to the nonce on the launch-ledger.jsonl line for pid 47624 (the 6th of 7 lines, launched_at_seconds=1791177551), and the ledger's launch_image equals launch.json's executed path (runs/bevy-round4/launch-image/8d228a52-69ad-4b5a-b4c7-20dbee2e839e/hof_game.exe). All three passes recorded (45884/0a2cdc41, 49108/cbff2566, 47624/faf2adda) match their own snapshot ledger lines and each was logged contemporaneously by the snapshot poller (F:/hof-r4c-logs/watch-battery2.log 11:52:36 / 12:46:02 / 13:19:27)."
  },
  {
   "id": "C2-identity-fields-computed-not-written",
   "pass": true,
   "evidence": "src/adapter/bevy/round.rs:508 and :794 `identity_fields(facts) = (facts.listening_pid, !facts.nonce.trim().is_empty())`; launch.rs:609-619 `listener_pid` parses `netstat -ano -p tcp` and `GameProcess::answering_pid` calls it; mod.rs:930-938 builds LaunchFacts with spawned_pid=Child::id() and listening_pid=process.answering_pid(). At commit 1c1aaef (round 3) the same block read `\"answering_pid\": facts.spawned_pid` and `\"verified\": true` (git show 1c1aaef:src/adapter/bevy/round.rs:512-513). Both round-3 literals are gone. Caveat RA-4: `verified` is derived from nonce non-emptiness, which every successful launch satisfies."
  },
  {
   "id": "C3-timing-arithmetic-no-stale-responder",
   "pass": true,
   "evidence": "Final pass: first battery read frame 473 at timestamp_ms 1791177561461, last frame 671 at 1791177564819 -> 198 frames / 3.358 s = 58.96 fps; implied process start 1791177553.439, i.e. 2.44 s AFTER the ledger line (1791177551) and equal within 57 ms to the game's own boot line in launch.json stop.stderr_tail (`boot frame=0 pid=47624 wall_ms=1791177553382`). The spawned child's own stderr also prints `liveness frame=470 pid=47624 wall_ms=1791177561391 elapsed_ms=8011`, 70 ms before call 0001 read frame 473. Pass-01 and pass-02 give the same shape: implied start 1791172339.349 (ledger 1791172337) and 1791175549.361 (ledger 1791175547), first frames 485 and 477, i.e. ~8 s of process life. Round 1's failure signature (implied start 26 s after run start, 3388 s before the first read, pid not matching either record) is absent."
  },
  {
   "id": "C4-no-survivors-no-endpoint-holder",
   "pass": true,
   "evidence": "runs/bevy-round4/round-stop.json: called_at_seconds 1791177759, recorded=[55932,45884,55944,49108,45808,47624,48168] (= all 7 ledger pids, verified as a set), reaped=[], still_alive=[], endpoint_holder=null, failure=null. My own reading at acceptance time: `netstat -ano | findstr \"15702 15703\"` no line; `tasklist /FI \"IMAGENAME eq hof_game.exe\"` and `hoh.exe` both `No tasks are running`."
  },
  {
   "id": "C5-nine-battery-steps-demonstrated",
   "pass": true,
   "evidence": "57 raw call files, all ok=true, error=null, seq 1..57. movement x 0.0(f493)->54.2306(f513) after move_dir=1@f497; coins 0(489)->1(523)->2(539); won false(491,525)->true(541,557,571,585); jump first -200.0, max -165.01016235351562, rising 4 / falling 8, 13 samples, back to -200.0 at f671 after jump_pressed=true@f641; grounded true at f473 and f481 with no injection yet; movement_left x 264.6115(595)->210.3435(613) after move_dir=-1@597; movement_release x byte-identical 203.63699340820312 at f623 and f635 after move_dir=0@615; win_position: call 20 at f543 >= the win frame 541; grounded_payload: call 8 carries Grounded{on_ground:true}. All nine also hold in pass-01 and pass-02 (rising 4 / falling 8 in all three; first frames 485/477/473)."
  },
  {
   "id": "C6-jump-has-rise-and-fall-and-grounded-before-takeoff",
   "pass": true,
   "evidence": "P4: the transform series f639..f671 is -200.0, -171.761, -168.129, -165.877, -165.010, -165.517, -167.378, -170.635, -175.305, -181.325, -188.813, -197.656, -200.0 -> 4 rising and 8 falling steps in every pass. P5: `bevy_grounded` is true at f637 (call 41) before `bevy_inject_jump` at f641, and the Grounded component carried inside every player_transform response is on_ground=false for f649..f669 and true again at f671, so PRD P5's both halves (true on the ground, false airborne) are in the raw payloads, not only asserted."
  },
  {
   "id": "C7-artifact-increment-real",
   "pass": true,
   "evidence": "I recomputed the tree digest myself (sha256 over sorted `relpath\\0sha256\\n`, .git/target excluded) over runs/round4/versions/<version_id>/: A0 638057ca.. = 272863b413d2dd64eed402de1962f1f30c8fac59f49ea94a1143e1d8c21f71cd (6 files), A1 a8a409d9.. = 8200d66e31fb09ca01d4ef32d2e3d8c19cfcfb6005cf2f14eabe1940e93ddf0c, A3 24f6ebe2.. = d6df52bcae86b718135c2f03c7fedcacc5e778a7c527db7fa7737d8b48db38b3 - all three equal to the report. A1 differs from A0 in src/game.rs (dfe4852c->3cf7e23e) and src/contract.rs (0c8df81d->76191ab1); Cargo.lock/Cargo.toml/src/main.rs are byte-identical across A0..A3."
  },
  {
   "id": "C8-artifact-gate-legitimate",
   "pass": true,
   "evidence": "runs/bevy-round4/gate.json {applicable:true, launchable:true, reasons:[]} is `evaluate_launchable` over real steps (src/adapter/mod.rs:59-91 requires editor_errors_baseline.ok && play_scene_ready.ok). The records are substantive: editor_errors_baseline = `the candidate built (1628 ms, 8 contract type path(s) declared: ... Player, Grounded, CoinCounter, WinFlag, FrameCounter, ProcessNonce, InputIntent, Transform; frozen feature set d6a90ba3...)` and play_scene_ready = `the game answered on http://127.0.0.1:15702/ after 2706 ms (pid 47624, headless); E3 ...=ok`. Not vacuous either way: the gate is `not_applicable` when a battery declares no gate step and red when a gate step is not ok (pinned by the round.rs gate tests, which pass in my run)."
  },
  {
   "id": "C9-executed-image-digest-real",
   "pass": true,
   "evidence": "I hashed the file: runs/bevy-round4/launch-image/8d228a52-.../hof_game.exe = 186,890,240 bytes, sha256 93a0cc09d10105f690981136e7ace65130fc70d046971613a0421cd625ef34ec, equal to launch.json's recorded built and executed digests and to the built F:/hof-bevy-r4-run/hof-bevy-shared-target/debug/hof_game.exe."
  },
  {
   "id": "C10-economics-reproduce",
   "pass": true,
   "evidence": "From runs/round4/iter-{1,2,3}/result.json: developer calls 69/125/102, tokens 2,626,195/13,091,431/5,223,211 (total 20,940,837), durations 1,174,089/3,020,012/1,723,260 ms; round total 26,484,181 (runs/round4/meta.json and the harness's final line). Round 2 developer 254 calls / 19,597,305 tokens / 93.3 min; round 3 developer 129 calls / 6,399,815 tokens / 52.5 min. All three round-4 Developer calls ended RepeatedActionError, never the step budget and never the 3600 s wall clock (`step_budget_exceeded` appears 0 times in the three trajectories; each trajectory does carry counted writes with `hoh_write_path`). The preserved runs/round4-attempt4 shows the wall clock binding instead: developer 143 calls / 11,442,096 tokens / 60.46 min / TimeExceeded."
  },
  {
   "id": "C11-cost-target-measured-honestly-and-not-met",
   "pass": false,
   "evidence": "The stated target is `total_tokens below 1500000` per Developer call (ROUND-2-REPORT.md:43, ROUND-3-REPORT.md:232). Round 4 per-call tokens are 2,626,195 / 13,091,431 / 5,223,211 - all far above 1.5M - and the round total (26,484,181) is the highest of the three rounds (round 2 21,619,239; round 3 12,362,478). The report states the 3.27x/2.29x ratios honestly. Earlier rounds were cheap for different reasons: round 3's 43/43/43 all ended LimitsExceeded because the gated value was frozen before the call (a broken cap), while round 2's 150 (LimitsExceeded at the flat ceiling) and 104 (TimeExceeded at the wall clock) were genuine limits. So the cost target is NOT met, and round 3's cheaper figure is not a valid comparator."
  },
  {
   "id": "C12-prd-coverage-and-transport-gap",
   "pass": true,
   "evidence": "Run line `prd coverage: 6/8 verified (total=derived from the Tester's claims...)`; per iteration 6 verified / 2 gaps: iter-1 gaps P2B+S1, iter-2 gaps S1+P3-goal-x, iter-3 gaps P3-goal-x+S1-deterministic-step. The denominator is the Tester's own 8 claims because no claim id matches the PRD's F1..F17 rule (src/model.rs:159-201), so 6/8 is self-referential and not comparable with round 3's 7/8 (see RA-5). Transport: round 3's surviving pass first call is ok=false, kind=transport, `BRP transport failure to http://127.0.0.1:15702/: transport failure` (runs/bevy-round3/calls/0001-bevy_grounded.json); all three round-4 passes' 171 calls are ok=true and each pass's first call is a successful grounded read at frame 473/485/477, so G-transport does not appear in any round-4 iteration and the transient itself is absent."
  },
  {
   "id": "C13-tree-gate-green",
   "pass": true,
   "evidence": "cwd F:/moonbit-hof-rs, CARGO_TARGET_DIR=F:/hof-acc-target (my own, empty at start), `cargo test --offline` -> literal exit code 0 (F:/hof-acc-logs/gate.exit = EXIT=0), 734 passed / 0 failed / 6 ignored / 740 listed over 56 `test result:` lines; `cargo test --offline -- --list` -> exit 0, 740 test names; `cargo fmt --all --check` -> exit 0 with no output. No other cargo/rustc/test process ran (tasklist checked before and after)."
  },
  {
   "id": "C14-zero-warnings-and-no-test-removed",
   "pass": true,
   "evidence": "`warning:` occurs 0 times in both the test stdout and the compile stderr (the 4 case-insensitive `warning` hits in stdout are test names such as `every_result_json_carries_the_scope_warning`). No test removed: my 740 sorted test names are byte-identical to the round's recorded gate-after-list.out, which is byte-identical to its gate-before-list.out, and the count rose from round 3's 723 to 740. The 6 ignored are exactly the real-engine tests (bevy_adapter_b1, bevy_adapter_b2, bevy_round1, brp_real_handover x3), enumerated with `--list --ignored`."
  },
  {
   "id": "C15-no-key-material-in-the-tracked-tree",
   "pass": true,
   "evidence": "I re-implemented the repository's own shape rule (KEY_PREFIXES sk-/sk_/pk-/ghp_/xoxb-/AKIA/AIza + >=16 token chars, or api_key/secret/... value >=32 chars; src/runtime/secrets.rs:146-213) and scanned all 179 tracked files plus the whole browsable tree (176 files, the same GENERATED exclusions as tests/credential_scan.rs) -> 0 findings, values never printed. config/model.secret.env is absent. The only key-shaped material left is the two pre-existing, gitignored evidence files the reports name (runs/round1/iter-1/traj/developer.attempt1.json and runs/round1b/iter-1/traj/tester.attempt1.json, fingerprint 5cf81e8f), which are not in the tracked tree."
  },
  {
   "id": "C16-secrets-load-only-from-outside",
   "pass": true,
   "evidence": "config/hoh.yaml carries no api_key value (only the comment that it must be empty); src/runtime/secrets.rs:327-348 `ensure_secret_file_is_outside` refuses a path inside the repository (and a parent of it), and the round loaded the key through `--env-from-secret F:/hof-secrets/round4.env` (round-4 run command), a path outside the tree. The refusal and the load are pinned by tests/credential_scan.rs, which pass in my gate."
  },
  {
   "id": "C17-frozen-documents-unmodified",
   "pass": true,
   "evidence": "`git diff HEAD` is empty for the whole tree, so every tracked document is exactly as committed. Last commit touching each: REQUIREMENTS/DESIGN-OVERVIEW/SPIKE-1/SPIKE-2 8535257, PRD  ba3d5c1, DESIGN-DETAIL/BATCH-B1/DECISIONS 6553afe, BATCH-B2 fca7647, BATCH-B3 ba3d5c1 and its acceptance 14bd50f, TRUST 81c72cd, ROUND-1 6ecc14f, ROUND-2 6355bc3, ROUND-3 1c1aaef, ROUND-4-REPORT a30cb7e (added, not modified), ROUND-4-REPORT-COMPLETE f7e87ee (added). No commit after the round touched any frozen document. PRD.md is still the 7819-byte file whose first 5136 bytes hash to dca329f3b09519b743a8f26890cbc8b9a61f4e1acc04a0d6a427b47387bf4527 (the SEALED_PREFIX_SHA256 literal in src/adapter/bevy/prd.rs) and whose full sha256 is 93b2ed85... - the value the round's own preflight printed."
  },
  {
   "id": "C18-tree-scope-and-nothing-pushed",
   "pass": true,
   "evidence": "Tracked tree = 179 files under .gitattributes/.githooks/.gitignore/.spec/config/scripts/src/tests + Cargo.toml/Cargo.lock/DECISIONS.md. godot-mcp/, .spec/hof-rs/, src/adapter/godot.rs and the Godot-only tests are gone (commit 14bd50f, declared in STRIP-REPORT.md); the residue is the two Godot skill prompt files and the Godot sections in planner.md/tester.md (RA-6). Push state from local refs only (offline): bevy-core has no upstream; refs/remotes/origin/master is still 6553afe (2026-10-04 03:25) while master is 2 commits ahead and bevy-core is 5+ ahead, so no Bevy work is pushed. Nothing staged or committed by me."
  }
 ],
 "defects": [
  {
   "id": "RA-1",
   "severity": "medium",
   "what": "The launch ledger is appended AFTER the spawn, not before it, although the ledger's own note, the doc comment on append_ledger and both round reports say 'written by the harness before the spawn'. The nonce itself IS generated before the spawn (launch.rs:368) and goes into the child's environment at :439, so the identity proof is unaffected; but the claim that the ledger line 'cannot be satisfied by copying a field inside launch.json' rests on an ordering that does not exist.",
   "reproduction": "src/adapter/bevy/launch.rs:443 `let mut child = command.spawn()` -> :450-455 `append_ledger(ledger, &ledger_entry(pid, ...))`; `pid` cannot exist before the spawn. Measured: ledger launched_at_seconds 1791177551 vs the child's own boot line wall_ms 1791177553382 (+2.38 s), consistent with the ledger being written at spawn time."
  },
  {
   "id": "RA-2",
   "severity": "low",
   "what": "runs/round4/ROUND-4-REPORT-COMPLETE.json battery.steps[e3_grounded_payload].proving_reading says 'a Grounded payload carrying a boolean at frame 477', but the cited file 0008-bevy_grounded.json carries frame 495, and no call in the pass reads frame 477 (frames present: 473,480,481,488,489,491,493,495,...). The verdict (a Grounded payload carrying a boolean) is still demonstrated.",
   "reproduction": "python over runs/bevy-round4/calls/*.json printing each call's result.frame and the contract::Grounded payload; grep for 477 in the 57 files."
  },
  {
   "id": "RA-3",
   "severity": "low",
   "what": "runs/round4/battery-snapshots/pass-0N/round-stop.json is the sweep that ran BEFORE pass N's launch, not that pass's own stop (it never lists pass N's pid), while the same directory's launch.json and ledger are from pass N or later. The report's description 'each pass as it was written' invites reading the snapshot's round-stop as that pass's stop. No evidence is fabricated; the snapshot is a coherent copy of the live directory taken ~20 s after the pass's launch.",
   "reproduction": "pass-01 round-stop called_at_seconds 1791172333 vs its own ledger line 1791172337; pass-02 ...542 vs ...547; pass-03 ...7545 vs ...7551, and in each case the pass pid is absent from `recorded`. The poller log F:/hof-r4c-logs/watch-battery2.log timestamps the three copies at 11:52:36 / 12:46:02 / 13:19:27, and pass-03's round-stop.json mtime 1791177547 precedes its launch.json mtime 1791177565."
  },
  {
   "id": "RA-4",
   "severity": "low",
   "what": "identity.verified is 'computed' only in form: round.rs:794 derives it as `!facts.nonce.trim().is_empty()`, and launch.rs:368 always generates a nonce (uuid v4) for a launch whose nonce was not fixed by a test. So for every launch that returns, verified is true; the field cannot distinguish anything on its own, and the only independent corroboration in the record is answering_pid. answering_pid and listening_pid are the same reading (both = facts.listening_pid), so asking whether they agree with each other is not a second witness; the genuine check is answering_pid vs spawned_pid.",
   "reproduction": "round.rs:794-805 and launch.rs:358-368; the unit test the_identity_fields_are_computed_from_the_facts_not_asserted only produces verified=false with a hand-built empty-nonce LaunchFacts, which no live path constructs."
  },
  {
   "id": "RA-5",
   "severity": "medium",
   "what": "The headline coverage figure '6/8 verified' has a self-referential denominator: no claim id is an F1..F17 id, so PrdCoverage::total() is the Tester's own claim count (6 verified + 2 gaps), not a fixed PRD item count. It therefore cannot be compared with round 3's 7/8, and it does not say that 6 of the PRD's 8 (or of P1..P5+C1..C6) are covered. The two round-4 gaps are real and stay open: P3-goal-x (the contract exposes no goal position, so 'the player reached the goal' is not checkable beyond the win flag flipping) and S1-deterministic-step (no persisted late-round liveness step under .hoh/deterministic/raw/).",
   "reproduction": "src/model.rs:188-208; runs/round4/iter-3/result.json prd_coverage; the grounded_world claim list in runs/round4/iter-3/evidence.json (verified P1..P5,S1; gaps P3-goal-x, S1-deterministic-step)."
  },
  {
   "id": "RA-6",
   "severity": "low",
   "what": "The tree is not only the harness plus the Bevy flow: src/prompts/skills/godot-dev.md and godot-testing.md are still compiled in (src/prompts/mod.rs:133-152) and are injected with the Bevy skills into every role, and the round-4 workspace shows them delivered during the round. STRIP-REPORT.md declares this residue and its reason, so it is disclosed rather than hidden, but the accepted tree still hands the roles 22.5 KB of a previous engine's instructions.",
   "reproduction": "ls -la F:/hof-bevy-r4-run/workspace/.hoh/skills/ -> godot-dev.md 17383 B and godot-testing.md 5158 B, mtime 2026-10-05 12:50 (during the reported round); src/prompts/mod.rs:146-152 skills()."
  },
  {
   "id": "RA-7",
   "severity": "low",
   "what": "DECISIONS.md has no round-3 or round-4 entry (the newest is D297, 2026-10-04), although round 4 changed enforced behaviour (the progress-following step budget, the action-key fold and restart-on-write, the computed identity fields, the ledger sweep, the client rebuild). The audit trail for those decisions lives only in the round report.",
   "reproduction": "grep -c 'round-4' DECISIONS.md = 0; `grep -n '^## D' DECISIONS.md | tail -1` = D297; DECISIONS.md's last commit is 6553afe."
  },
  {
   "id": "RA-8",
   "severity": "low",
   "what": "One of the nine battery steps is definitional: e3_win_position ('a transform sample at or after the win frame') is satisfied by any in-order transform read after the win, and e3_grounded_payload is an existence check for a payload shape. Both verdicts are honest, but they add no discriminating power and should not be counted as two of nine behavioural proofs.",
   "reproduction": "runs/bevy-round4 calls 20 (transform f543 >= win f541) and 8 (Grounded payload with a bool); the step definitions are in ROUND-4-REPORT-COMPLETE battery.steps."
  },
  {
   "id": "RA-9",
   "severity": "low",
   "what": "parse_listener_pid prefers a LISTEN line but, when none matches, returns the first pid whose local address ends in :port, so answering_pid can name a socket holder that is not LISTENing. Not exercised in this round (47624 was the LISTENer), but it weakens 'the OS TCP table's listener reading' as a phrase.",
   "reproduction": "src/adapter/engine.rs:195-219 (the `candidate.get_or_insert(pid)` fallback)."
  }
 ],
 "risks": [
  "The identity proof is enforced by code (a nonce mismatch fails readiness) but is not reproducible from launch.json alone: the record shows a nonce that only this spawn's environment could carry, and the read-back itself leaves no per-launch trace. A reader can only re-derive it by reading launch.rs, not from the evidence.",
  "The round's Go/No-Go rests on one completed round (attempt 6). E4 asks for reproducibility from two runs, and five earlier attempts failed for contract or infrastructure reasons; the two earlier failures that were not the harness's fault (attempt4's connector failure, attempt5's Tester writing into the frozen candidate) are single observations.",
  "Six tests are ignored in the gate, and they are exactly the ones that would exercise the real-engine contract, the readiness handshake and the client rebind across two real launches. The launcher's identity handshake is therefore still unexercised by the gate.",
  "No live negative control: nothing drove a monotone fall to show it is not counted as a jump; that rests on unit tests inside the gate (rounds 2 and 3 recorded the same limitation).",
  "The binding limit on a producing Developer call is now the repeated-action tripwire (max_repeated_actions=15): it fired 3/3 at 69/125/102 calls on a folded build+test loop, so the progress gate's ceiling of 150 was never reached, and the tripwire is what decides how much work a producing call gets.",
  "The cost target (below 1.5M tokens per Developer call) is not met and no round has met it; the trend across rounds 2->3->4 is a function of which cap was binding, not of a cost reduction.",
  "Push state was verified from local refs only (no network): bevy-core has no upstream and origin/master is older than both master's last two commits and all of bevy-core."
 ],
 "unverified": [
  "That the answering process really served this launch's nonce over the wire in this round: I verified the code path (readiness calls world.get_resources for hof_game::contract::ProcessNonce and refuses a mismatch) and the recorded nonce, but the record cannot show the read-back.",
  "Byte-identity of the frozen semantic type paths in A1: the Developer changed src/contract.rs between A0 and A1. The build step records 8 declared contract type paths and the adapter's contract hash is unchanged (c579a742...), but I did not diff A0's and A1's contract.rs against the frozen path list.",
  "E4 reproducibility: only one completed round exists, so 'the same command rerun in a clean environment gives the same class of result' is not established.",
  "The six-attempt token aggregate (60,963,711): I reproduced attempt1 9,380,879, attempt5 9,656,871, round4 26,484,181 and attempt4's completed iteration 14,022,468 from result.json usage; the report's attempt4 14,589,317, attempt2 425,915 and attempt3 426,548 (which have no result.json) could not be located, and the four reported components do sum to the reported total.",
  "The reasons the earlier attempts failed as contract checks (attempt1 no_engineering_write, attempt5 qa_contaminated_candidate) beyond their exit codes and the report's text: I did not re-read those attempts' contract-check evidence.",
  "Whether nothing was ever pushed: verified from local remote-tracking refs and the absence of an upstream only, because the acceptance is offline."
 ]
}

---

# ACCEPTANCE — rounds 1..4 (the round-4 evidence, its battery, its artifact, its economics, the tree gate and the forbidden zones)

- Date: 2026-10-05
- Acceptance agent: an independent subagent, no prior context, no implementer or dispatcher conclusion inherited
- Revision measured: branch `bevy-core`, **HEAD `f7e87ee`**; `git status --porcelain` and `git diff HEAD` both empty
- Environment: offline; **no engine, no game, no network, no model call and no round was run**; nothing written under `runs/**`; no tracked file modified; my scripts and logs live under `F:/hof-acc-work` and `F:/hof-acc-logs`, and my build directory is `F:/hof-acc-target`
- The block above is the output of a Python `json.dumps`, written as the head of this file and then read back out of the written file with `json.loads` before this prose was appended (criteria/defects counts asserted equal).

## 1. Per-item table

| # | Job | Judgement | What I established myself |
|---|---|---|---|
| 1 | round-4 evidence internally consistent and attributable | **pass** (defect RA-1, RA-4) | The answering nonce equals the ledger line written for that pid; the three pids are equal and come from `netstat -ano -p tcp`; the fields are computed (round 3's two literals are gone); `round-stop.json` records 7 pids, 0 survivors, no endpoint holder, and I re-checked live that nothing holds 15702 |
| 2 | the timing arithmetic (the field that caught rounds 1 and 2) | **pass** | Frame/wall-clock reconstruction gives an implied process start 2.44 s *after* the ledger line, matching the game's own boot line within 57 ms, and the spawned child's stderr names the same pid and frame; 473 frames (~8 s) behind the first read in pass 3, 485 and 477 in passes 1 and 2 |
| 3 | the nine battery steps against the raw calls | **pass** (defect RA-2, RA-8) | All 57 calls `ok`, every cited reading reproduced from the frames/values; jump rising 4 / falling 8 in all three passes; grounded true before take-off and false airborne in the raw payloads; `e3_grounded_payload`'s cited frame is wrong (495, not 477) |
| 4 | the artifact and the fingerprint | **pass** | I recomputed the A0/A1/A3 tree digests byte-for-byte with the stated rule and they match; A1 differs from A0 in `src/game.rs` and `src/contract.rs`; lockfile/toml/main unchanged |
| 5 | the artifact gate is legitimate rather than vacuous | **pass** | The gate is `editor_errors_baseline.ok && play_scene_ready.ok` over substantive records (a real 1628 ms build declaring 8 contract paths, and a real answered endpoint at pid 47624); the gate is `not_applicable` without the steps and red when one is not ok |
| 6 | the economics, stated fairly | **pass for the figures, fail for the target** (criterion `C11-cost-target-measured-honestly-and-not-met`) | Developer 296 calls / 20,940,837 tokens / 98.6 min over three calls of 69/125/102, all ended by `RepeatedActionError`; round 2 254/19,597,305; round 3 129/6,399,815 (all three capped at 43 by a frozen gate value) |
| 7 | PRD coverage and the transport gap | **pass, with a caveat** (RA-5) | `6/8` where the 8 is the Tester's own claim count; final gaps `P3-goal-x` and `S1-deterministic-step`; no transport failure in any of the three round-4 passes (0/171 calls), against round 3's first call failing at the transport layer |
| 8 | the tree gate | **pass** | `cargo test --offline` literal exit **0**, **734 passed / 0 failed / 6 ignored / 740 listed**, 56 result lines, **0 `warning:`**; `--list` exit 0 with 740 names; `cargo fmt --all --check` exit 0; no second test process |
| 9 | hard constraints and forbidden zones | **pass** (defect RA-6, RA-7) | 0 key-shaped findings in the tracked tree by the repository's own rule; the key loads only from outside; every frozen document is unmodified and the PRD still seals at byte 5136; the tree is the harness plus the Bevy flow with a declared Godot prompt residue; nothing pushed |

## 2. Job 1 — identity and attributability

**The facts in `runs/bevy-round4/launch.json`.** `identity.spawned_pid = identity.answering_pid = identity.listening_pid = 47624`; `identity.nonce = faf2adda-c698-48ef-a4f5-f51d1da551c6`; `identity.verified = true`; `stop = {exit_code: 0, pid_dead: true, grace_millis: 5000}`; `client_generation = 1`.

**The cross-check against the ledger.** `runs/bevy-round4/launch-ledger.jsonl` has 7 lines; line 6 is the only line for pid 47624, nonce `faf2adda-…`, launch_image `runs\bevy-round4\launch-image\8d228a52-…\hof_game.exe` — both equal to `launch.json`. The other six lines have six different nonces, and no other line names 47624.

**Where each field comes from (computed, not written).**

* `spawned_pid` is `Child::id()` (launch.rs:447), the pid the harness started.
* `listening_pid` is `GameProcess::answering_pid()` (launch.rs:269-275) → `listener_pid(port)` (launch.rs:609-619) → `netstat -ano -p tcp` parsed positionally with a `LISTEN` preference (`parse_listener_pid`, engine.rs:195-219).
* `answering_pid` in `launch.json` is `facts.listening_pid` (`identity_fields`, round.rs:794) — i.e. the same OS reading, not a copy of `spawned_pid`. It *can* be absent and it *can* disagree; the unit test pins the disagreement case.
* `verified` is `!facts.nonce.trim().is_empty()` (round.rs:795), and a launch only returns after readiness read `hof_game::contract::ProcessNonce` back over the wire and compared it to this launch's nonce (launch.rs:502-529); a mismatch returns `LaunchError::IdentityMismatch`.
* At commit `1c1aaef` (round 3) the same object read `"answering_pid": facts.spawned_pid` and `"verified": true` — two literals. `git show 1c1aaef:src/adapter/bevy/round.rs` proves the change. Round 3's `runs/bevy-round3/launch.json` shows the old shape (no `verified_rule`, no `client_generation`).

So: **yes, all four fields are computed, and two of them (the nonce cross-check against the ledger, and the OS listener reading) are independent of the harness's own hope.** The one honest qualification is RA-4: `verified` is a predicate over a field that is invariant for every successful launch, so it is derived but cannot discriminate; the discriminating evidence is the nonce itself plus `answering_pid`.

**Round-end.** `round-stop.json` records all seven ledger pids, `reaped: []`, `still_alive: []`, `endpoint_holder: null`, `failure: null` (called at 1791177759, 190 s after the last launch). Round 3 left pid 54568 (the last line of its ledger) alive and has no round-stop file at all; round 4's sweep covers it. At acceptance time I re-read the machine myself: no `netstat` line for 15702/15703, and no `hof_game.exe`/`hoh.exe`/`cargo.exe`/`rustc.exe` running.

## 3. Job 2 — the timing arithmetic, and could a stale process have answered?

This is the arithmetic that caught rounds 1 and 2 (TRUST-REPORT §3: round 1's answering process had begun counting frames 26 s after `hoh run` started, 3388 s before the battery read it, and its pid matched neither record).

For round 4's final pass, from the raw calls and the game's own stderr in `launch.json`:

| quantity | value | source |
|---|---|---|
| first battery read | frame **473** at `timestamp_ms` 1791177561461 | `calls/0001-bevy_grounded.json` |
| last battery read | frame **671** at 1791177564819 | `calls/0057-bevy_player_transform.json` |
| frames/second in the window | **58.96** (198 frames / 3.358 s) | recomputed |
| implied process start | **1791177553.439** | `first − 473/58.96` |
| ledger line for pid 47624 | **1791177551** | `launch-ledger.jsonl` line 6 |
| implied start − ledger | **+2.44 s** | |
| the game's own boot line | `boot frame=0 pid=47624 wall_ms=1791177553382` | `launch.json` `stop.stderr_tail` |
| implied start − boot line | **+0.057 s** | |
| the child's own last liveness line | `frame=470 pid=47624 wall_ms=1791177561391 elapsed_ms=8011` | same |
| first call − that line | **70 ms**, and 470 vs 473 frames | same |

Pass-01 and pass-02 reconstruct the same way (implied starts 1791172339.349 and 1791175549.361 against ledger lines 1791172337 and 1791175547; first frames 485 and 477, i.e. ~8.2 s and ~8.1 s of process life). A stale process answering this endpoint would show hundreds of thousands of frames behind the first read; here the answering process is **8 seconds old**, its own stderr (read from the child's pipe by the harness) names pid 47624, and its frame count at 1791177561.391 is 470 against the battery's 473 read 70 ms later.

**Conclusion: nothing in this round could have been answered by a stale process** on the recorded evidence, and the nonce makes it structurally impossible — a process spawned before this launch cannot know a UUIDv4 created in the harness 2.4 s earlier and passed only through this child's environment. The one thing I cannot re-derive from the record is the read-back itself (see `unverified`): that is a code-level guarantee enforced in `start_game`, not a fact `launch.json` can show.

Defect **RA-1** belongs here: the ledger line is appended *after* the spawn (`launch.rs:443` spawn → `:450` `append_ledger`), although the line's own note and both reports say "before the spawn". `pid` cannot exist before the spawn; the nonce does (`:368`, before the free-port check and before staging). The identity proof is therefore unaffected, but the documented ordering is wrong and part of the report's argument for it is not sound.

## 4. Job 3 — the nine battery steps, read from the raw calls

57 files in `runs/bevy-round4/calls/`, every one `ok: true`, `error: null`, `seq` 1..57, each carrying its own `timestamp_ms`. I re-read the frames and values from the JSON rather than the summary:

| step | verdict in the report | what the raw calls show | demonstrated? |
|---|---|---|---|
| `e3_movement` (P1) | pass | `bevy_inject_move move_dir=1` at f497 (call 9); x 0.0 at f493 (call 7) → 54.23064041137695 at f513 (call 11) | yes |
| `e3_coin_counter` (P2) | pass | coins 0 at f489 (call 5) → 1 at f523 (call 14) → 2 at f539 (call 18), `target: 2` | yes |
| `e3_win_flag` (P3) | pass | won false at f491/f525 (calls 6/15) → true at f541/557/571/585 (calls 19/23/26/29) | yes |
| `e3_jump_arc` (P4) | pass | `jump_pressed=true` at f641 (call 43); y −200.0 (f639) → −171.761 (f649) → max −165.01016235351562 (f655) → −200.0 (f671); **rising 4, falling 8** | yes |
| `e3_grounded` (P5) | pass | `bevy_grounded` true at f473 (call 1) and f481 (call 3), both before any injection | yes |
| `e3_movement_left` (P1) | pass | `move_dir=-1` at f597 (call 33); x 264.6115417480469 (f595) → 210.34353637695312 (f613) | yes |
| `e3_movement_release` (P1) | pass | `move_dir=0` at f615 (call 36); x byte-identical 203.63699340820312 at f623 (call 38) and f635 (call 40) | yes |
| `e3_win_position` (P3) | pass | win at f541; a transform read at f543 (call 20, x 115.19129943847656) | yes, but **definitional** (RA-8) |
| `e3_grounded_payload` (P5) | pass | call 8 carries `hof_game::contract::Grounded {on_ground: true}` — at **f495**, not the report's 477 (RA-2) | yes |

The report's other eight `proving_reading` strings reproduce exactly. All nine also hold in the two snapshot passes (57 calls each; the same arcs with rising 4 / falling 8; first frames 485 and 477).

**Which steps are asserted rather than demonstrated: none.** Every verdict is backed by a raw request/response pair. Two steps are weak by construction (`e3_win_position`, `e3_grounded_payload`): they are existence checks that an in-order battery satisfies automatically. And note what the step *set* does not show: PRD P5's airborne-false half is not a declared step, but it is in the raw data (the Grounded component travels inside every `player_transform` response: true at f473..f639, **false at f649..f669**, true again at f671), so the Tester's P5 claim citing f649 `grounded=false` is supported by the battery's own payloads.

## 5. Job 4 — the artifact, and the gate

**Increment (E1).** I recomputed the digest myself from the bytes with the stated rule (sha256 over sorted `relpath\0sha256\n`, `.git`/`target` excluded) — every version tree has exactly 6 files:

| version | tree digest (mine = the report's) | files that differ from the previous |
|---|---|---|
| A0 `638057ca…` | `272863b413d2dd64eed402de1962f1f30c8fac59f49ea94a1143e1d8c21f71cd` | — |
| A1 `a8a409d9…` | `8200d66e31fb09ca01d4ef32d2e3d8c19cfcfb6005cf2f14eabe1940e93ddf0c` | `src/game.rs` `dfe4852c`→`3cf7e23e`, `src/contract.rs` `0c8df81d`→`76191ab1` |
| A2 `ba935abe…` | `7fff09ba004e3aa08134d1da0a0865376b015124a16c2e9954519fd11f4c2168` | `src/game.rs` `3cf7e23e`→`ebaa1e58` |
| A3 `24f6ebe2…` | `d6df52bcae86b718135c2f03c7fedcacc5e778a7c527db7fa7737d8b48db38b3` | `src/game.rs` `ebaa1e58`→`b97feb48` |

`Cargo.lock`, `Cargo.toml` and `src/main.rs` are byte-identical across A0..A3, so `A_1 ≠ A_0` is a real engineering increment and the feature/lock contract did not drift.

**Gate (`runs/bevy-round4/gate.json`).** `{"applicable": true, "launchable": true, "reasons": []}`. Legitimate, not vacuous: the two gate steps are real records — `editor_errors_baseline: "the candidate built (1628 ms, 8 contract type path(s) declared: …; frozen feature set d6a90ba3…)"` and `play_scene_ready: "the game answered on http://127.0.0.1:15702/ after 2706 ms (pid 47624, headless); E3 movement=ok …"` — and `evaluate_launchable` returns `not_applicable` when a battery declares no gate step and `launchable: false` with reasons when one is not ok (pinned by the `RoundReport::evaluate` tests, all green in my gate). What the gate does **not** prove is attribution: it would be green for a stale responder exactly as in rounds 1 and 2. That is what `launch.json`'s identity object and the arithmetic above are for.

The executed image is real: I hashed `runs/bevy-round4/launch-image/8d228a52-…/hof_game.exe` (186,890,240 bytes) → `93a0cc09d10105f690981136e7ace65130fc70d046971613a0421cd625ef34ec`, equal to both digests in `launch.json` and to the built binary.

## 6. Job 5 — the economics, stated fairly

| | developer calls | wall clock | developer tokens | round tokens | ended by |
|---|---|---|---|---|---|
| round 2 | 150 + 104 = **254** | 93.3 min | **19,597,305** | 21,619,239 | iter-1 `LimitsExceeded` at 150; iter-2 `TimeExceeded` at the 3600 s clock |
| round 3 | 43/43/43 = **129** | 52.5 min | **6,399,815** | 12,362,478 | all three `LimitsExceeded` at exactly 43 (the gated value was frozen before the call) |
| round 4 | 69/125/102 = **296** | 98.6 min | **20,940,837** | **26,484,181** | all three `RepeatedActionError`, never the budget, never the wall clock |

All figures are from `runs/round{2,3,4}/iter-*/result.json` usage blocks, which I read directly; the round-4 total also appears in the harness's own final line and `runs/round4/meta.json` (exit 0, `game_endpoint` pid 47624, nonce `faf2adda…`, `source: launch_verified`).

**What ended each call.** Round 4: `step_budget_exceeded` appears 0 times in the three developer trajectories; each trajectory does contain counted project writes (`hoh_write_path` 6/23/11 times) and each call ran past the ungated 43, so the progress gate did lift to its 150 ceiling; nothing reached 150 because the tripwire cut at 15 repeats of one folded build+test action (the verbatim abort text is in the trajectories and matches the report). The preserved `runs/round4-attempt4` shows the other limit binding: developer 143 calls / 11,442,096 tokens / 60.46 min / `TimeExceeded`, exit 5.

**Is the goal's cost target met? No.** The target on record is *below 1,500,000 tokens per Developer call* (ROUND-2-REPORT:43; ROUND-3-REPORT:232). Round 4's per-call figures are 2.63M, 13.09M and 5.22M — none is within an order of magnitude of the target for iteration 2 — and the round total is the **highest** of the three rounds. The report itself does not claim otherwise; it states the 3.27×/2.29× ratios and calls the increase "the cost of the budget actually following progress".

**Were the earlier cheaper rounds cheap only because a broken cap truncated their calls?**

* **Round 3: yes.** All three Developer calls ended at exactly 43 calls / `LimitsExceeded` for the same reason the report gives (the gated value was read once before the call and frozen), so round 3's 6.4M is the cost of ~29 % of a call each. It is not a like-for-like comparator.
* **Round 2: no.** Its two calls hit real limits — 150 (the flat ceiling, with 11.1M prompt tokens of genuine grind) and 104 (`TimeExceeded` at 60.2 min). Round 2 is the only honest baseline, and round 4's developer is 20.94M vs 19.60M (+7 %) for the same three iterations while the round total is 26.48M vs 21.62M (+22 %, driven by more expensive Planner/Tester work).

So the fair statement is: **round 4 is the most expensive round so far, the per-call target is not met, and the round-3 comparison in the report is labelled but would be misleading if read as progress.**

## 7. Job 6 — PRD coverage and the transport gap

* Run line: **`prd coverage: 6/8 verified (total=derived from the Tester's claims; harness/gate describe the runtime contract, not the product)`**.
* Per iteration, 6 verified / 2 gaps: iter-1 gaps `P2B`, `S1`; iter-2 gaps `S1`, `P3-goal-x`; iter-3 gaps **`P3-goal-x`**, **`S1-deterministic-step`**.
* The denominator is not the PRD: `is_prd_functional_id` only recognises `F1..F17` (`model.rs:158-167`), no round-4 claim id is one, so `total()` = verified + gap = the Tester's own 8 claims. `6/8` therefore says "the Tester wrote 8 claims and verified 6", nothing about absolute PRD coverage, and it is not comparable with round 3's `7/8` (whose claim ids were also different: `C1-launch`, `P1-move-right`, …). This is RA-5, and the report's own note says it is not a like-for-like comparison.
* The two open gaps are substantive: `P3-goal-x` (the frozen contract exposes no goal position, so nothing beyond the win flag flipping can be checked about "reaching the goal") and `S1-deterministic-step` (no persisted late-round liveness step under `.hoh/deterministic/raw/`). The Tester's own S1 claim was verified through its own late `bevy_health` read at frame 6062, not through a battery step.
* **Transport: genuinely closed in the recorded evidence.** Round 3's surviving pass begins with `ok: false`, `kind: transport`, `BRP transport failure to http://127.0.0.1:15702/: transport failure` (`runs/bevy-round3/calls/0001-bevy_grounded.json`). All three round-4 passes have 57 `ok: true` calls (171/171) and each pass's first call is a successful `bevy_grounded` read at frame 473 / 485 / 477 — never frame 0, never an error. `client_generation: 1` in all three launches is consistent with the client being rebuilt at every launch (the field is per-peer, so it cannot show the cross-pass effect directly; the code at `mod.rs:478-483` and `:927` is what does). Caveat: the closure rests on one round's three passes, and the test that pins the call site is ignored in the gate.

## 8. Job 7 — the gate for the tree I am accepting

Run by me, in my own build directory, with the round's working tree untouched (`git status` empty before and after):

| command | literal exit code | counts |
|---|---|---|
| `cargo test --offline` (cwd `F:/moonbit-hof-rs`, `CARGO_TARGET_DIR=F:/hof-acc-target`) | **0** (`F:/hof-acc-logs/gate.exit` = `EXIT=0`) | **734 passed / 0 failed / 6 ignored / 740 listed** over **56** `test result:` lines, **0 `warning:`** |
| `cargo test --offline -- --list` | **0** | **740** test names |
| `cargo fmt --all --check` | **0** | no output |

* **Listed = passed + ignored** (734 + 6 = 740).
* **No test removed**: my 740 sorted names are byte-identical to `F:/hof-r4c-logs/gate-after-list.out`, which is byte-identical to `gate-before-list.out`; the count rose from round 3's 723.
* **The 6 ignored** (`--list --ignored`): `the_pinned_endpoint_answers_discover_with_the_23_methods_of_bevy_0191`, `the_real_machine_smoke_proves_the_contract_on_a_live_bevy_game`, `the_five_behaviours_are_observed_on_a_real_bevy_game_process`, `a_client_rebuilt_for_the_new_process_answers_on_its_first_call`, `the_adapter_rebinds_its_observing_client_at_every_launch`, `the_round_three_transport_failure_reproduces_through_one_client` — exactly the real-engine set the report names.
* **Zero warnings** in both the stdout and the compile stderr: the string `warning:` does not occur; the four case-insensitive hits are test names.
* **No second test process**: `tasklist` shows no `cargo.exe`, `rustc.exe`, `hof_game.exe` or `hoh.exe` before and after, and no `netstat` line for 15702/15703.

## 9. Job 8 — hard constraints and forbidden zones

* **No key-shaped material in the tracked tree (or the browsable tree).** I re-implemented the repository's own rule from its constants (`src/runtime/secrets.rs:146-213`) and ran it in Python over all **179 tracked files** and over the **176-file** browsable tree (the same `.git`/`target`/`.workspace`/`runs`/`node_modules` exclusions as `tests/credential_scan.rs`): **0 findings**, matched values never printed. `config/model.secret.env` does not exist. The only key-shaped material left is the two pre-existing, gitignored evidence files the reports name — `runs/round1/iter-1/traj/developer.attempt1.json` and `runs/round1b/iter-1/traj/tester.attempt1.json`, fingerprint `5cf81e8f` — which are outside the tracked tree and still need the key rotated by its owner.
* **Secrets load only from outside the repository.** `config/hoh.yaml` carries no `api_key` value; `ensure_secret_file_is_outside` refuses a path inside (or a parent of) the repository; the round used `--env-from-secret F:/hof-secrets/round4.env`, which is outside the tree and never printed. The refusal and the load are pinned and green in my gate.
* **Frozen documents unmodified.** `git diff HEAD` is empty; each frozen document's last commit predates every round commit and no commit after the round touched one (details in the JSON `C17`). `PRD.md` is still 7,819 bytes, its first 5,136 bytes hash to the `SEALED_PREFIX_SHA256` literal `dca329f3…` recorded in `src/adapter/bevy/prd.rs`, and its full sha256 (`93b2ed85…`) is the value the round's preflight printed.
* **Tree scope / nothing pushed.** 179 tracked files; the Godot engine clone, `.spec/hof-rs/`, the Godot adapter module and the Godot-only tests are gone (commit `14bd50f`, declared in `STRIP-REPORT.md`, which also explains why the two Godot skill prompt files remain — RA-6). `bevy-core` has no upstream; `refs/remotes/origin/master` is still `6553afe` (2026-10-04 03:25) while `master` is two commits ahead and `bevy-core` is further ahead, so no Bevy work is pushed. I did not stage, commit or push anything.

## 10. My own counterexamples and boundary probes

1. **Can a stale process explain the readings?** Reconstructed the process start from frame count and wall clock in all three passes and cross-checked it against (a) the ledger line and (b) the child's own stderr lines carrying its pid and frame count. A stale responder would need to satisfy all three simultaneously; it cannot.
2. **Is `verified` more than a restatement?** Traced the predicate to `!nonce.trim().is_empty()` and `new_process_nonce()` before the spawn → for every launch that returns, `verified` is true. The unit test only falsifies it with a hand-built empty-nonce record. Recorded as RA-4.
3. **Is PRD P5's airborne half asserted rather than demonstrated?** I initially suspected it (no `bevy_grounded` call during flight); checking the *whole* response payload showed the `Grounded` component inside every `player_transform` reply with `on_ground: false` for f649..f669 and `true` at f671. The claim is demonstrated — by a payload the step verdict does not surface.
4. **Does frame 477 exist?** Searched all 57 calls for it to test the `e3_grounded_payload` reading: it appears nowhere; the cited call is frame 495 (RA-2).
5. **First call of each pass**: re-read `calls/0001-*.json` for all three passes — all `ok: true`; compared with round 3's `0001` (`ok: false`, transport). The closure is measured, not inferred from the absence of a gap id.
6. **Gate negative behaviour**: read `evaluate_launchable` and confirmed it is `not_applicable` without the gate steps and red when one is not ok, so `reasons: []` is a real pass and not an empty record.
7. **Digest reality**: recomputed the version-tree digests and the 186 MB launch image digest from bytes; all match the records.
8. **Test list**: compared my independently produced 740 names with the round's before/after lists — identical.
9. **Live state**: no endpoint holder, no game/harness process, no second test process.

## 11. Independent judgement

The round-4 evidence is **internally consistent and attributable**, and this is the first bevy batch where I can say that from the record rather than from the author's assurance. The chain is: the ledger names a fresh UUID and a pid; the launcher generates that UUID before the spawn and puts it only in the child's environment; readiness refuses any other value; the same UUID appears in `launch.json` next to a pid read from the kernel's TCP table; and the arithmetic puts the answering process 2.4 s after that ledger line, 8 s old at the first read, with its own stderr naming the same pid and frame. Rounds 1 and 2 failed exactly here, and the field that caught them now passes by a wide margin in all three passes.

The nine battery steps are demonstrated by raw calls, the artifact is a real increment (my own digests), and the gate is green on a tree I built and tested myself in a fresh directory: **exit 0, 734/0/6/740, 56 result lines, zero warnings, `--list` 740, `fmt --check` exit 0**, with no test removed and no other test process.

The defects are real but none of them overturns those conclusions. The most substantive are RA-1 (the ledger is written after the spawn although the record and the reports say before it — the identity proof survives, the argument for it does not), RA-4 (`verified` is computed but cannot discriminate; `answering_pid` is the only independent corroboration), RA-5 (`6/8` is a self-referential ratio and two genuine gaps remain open) and RA-6 (a previous engine's instructions are still delivered to the roles). RA-2 and RA-3 are accuracy defects in secondary material: one wrong frame number and a snapshot whose `round-stop.json` is the sweep that preceded the pass.

The economics deserve the plainest statement: **the cost target is not met.** Round 4 is the most expensive round (26.48M tokens, 296 Developer calls) and its per-call figures are 1.8× to 8.7× the 1.5M target. Round 3's cheaper number was bought by a cap that froze at 43 and truncated every producing call, so the only fair comparator is round 2, against which round 4 is ~7 % more expensive per Developer call and ~22 % more expensive per round. The report says this; what the round does not yet show is any move toward the target.

## 12. What I could not verify

* That this launch's nonce was actually read back over the wire: the record cannot show it, and I did not run a game. It is a code-level guarantee (`launch.rs:502-529`) plus the recorded value.
* Byte-identity of the frozen semantic type paths in `A1`: the Developer rewrote `src/contract.rs`; the build declares 8 contract paths and the adapter's contract hash is unchanged (`c579a742…`), but I did not diff the two `contract.rs` revisions against the frozen path list.
* E4 reproducibility: one completed round is not two, so "the same command rerun in a clean environment gives the same class of result" is not established by me.
* The six-attempt token aggregate: I reproduced attempt 1 (9,380,879), attempt 4's completed iteration (14,022,468), attempt 5 (9,656,871) and the round (26,484,181) from `result.json`; the report's attempt-4 figure (14,589,317, which includes the iteration that died leaving no `result.json`), attempt 2 (425,915) and attempt 3 (426,548) are arithmetically consistent with the reported total (60,963,711) but I could not locate them in the preserved evidence.
* The contract-check details of attempt 1's `no_engineering_write` and attempt 5's `qa_contaminated_candidate`: I verified the exit codes and read the report's description, not those attempts' own check evidence.
* Whether nothing was ever pushed, to the extent that this is a statement about the remote: verified from local refs and the absence of an upstream, because the acceptance is offline.

## 13. Reproduction

Every number above came from files in this repository or from a command I ran; nothing was inferred from the reports where a raw file exists.

* Round evidence: `runs/bevy-round4/launch.json`, `launch-ledger.jsonl`, `round-stop.json`, `meta.json`, `gate.json`, `calls/0001..0057-*.json`, `readings/`, `launch-image/8d228a52-…/hof_game.exe`.
* Snapshots and their poller: `runs/round4/battery-snapshots/pass-01..03/`, `F:/hof-r4c-logs/watch-battery2.log`.
* Rounds 2/3: `runs/round{2,3}/iter-*/result.json`, `runs/bevy-round3/launch.json`, `runs/bevy-round3/calls/0001-bevy_grounded.json`, `runs/bevy-round3/launch-ledger.jsonl`.
* Preserved attempts: `runs/round4-attempt{1,2,3,4,5}/exit_code` and `iter-*/result.json`.
* Gate logs: `F:/hof-acc-logs/gate.out`, `gate.err`, `gate.exit`, `list.out`, `list.exit`, `fmt.exit`; helper scripts in `F:/hof-acc-work/`.
* My only write inside the repository is this file. Nothing was staged, committed or pushed; no `rm -rf` was used; no process was killed; nothing under `runs/**` was written.
