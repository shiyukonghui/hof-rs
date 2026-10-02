```json
{
  "task": "TASK-DR84-ACCEPTANCE",
  "kind": "independent acceptance of the TASK-DR84 offline batch; no engine, no round, no network; nothing staged, committed or pushed by me; nothing written under runs/**",
  "task_book": "none: the batch was dispatched as a self-contained prompt (there is no .spec/hof-rs/tasks/TASK-DR84.md; verified by listing the tasks directory)",
  "reviewed_report": ".spec/hof-rs/tasks/TASK-DR84-REPORT.md",
  "reviewed_report_sha256": "31fb5510f8965423598d19aeeb61bef79c7eccd29782263defb3be00eb1da4f7",
  "reviewed_report_bytes": 46327,
  "reviewed_report_note": "the file I reviewed is the working copy (46,327 B, sha256 31fb5510...); it is the committed revision (44,892 B, sha256 8a37faa7...) plus an 18-line section 11 post-note that the dispatcher appended at 01:26, after the local commit 930229b was made at 01:25.  Section 11 itself discloses that commit and the stale head, so the machine block's head value is stale in the report's own words, not silently",
  "head_at_acceptance": "930229bba7cfffb9a5e3964dd36536bd477fb39e",
  "origin_master_at_acceptance": "e56b712da0cbd8f7c4fe3a83bfaaec24315320ae",
  "pushed": false,
  "verdict": "pass",
  "verdict_scope": "All five items of my brief hold under my own instruments, with two major defects recorded that do not invalidate the batch's deliverable.  (1) The ordering is real and is now the rule the previous acceptance asked for: run() drives step_input_jump before interaction_evidence, input_channel_probe and input_replay, and the pin reads the named constants GROUND_NEEDING_BATTERY_STEP / GROUND_CONSUMING_BATTERY_STEPS instead of a literal action name; the coin rule is untouched and my own ordering plant leaves the coin test green while reddening the intended ordering test.  (2) Of the four false-confirmation shapes the previous acceptance listed, the first three cannot be produced by this change (I read the code paths and reproduced the fail-closed plant); the fourth (the two-frame flat-y proxy certifying a player who is not on a floor) is unchanged and remains possible in principle, but the reorder removes the shape in which the battery's own earlier jump supplied the apex.  (3) The arc rule and the fail-closed ground probe are byte-identical (both redden under my plants at the published lines), no criterion moved, the byte-frozen PRD and REQUIREMENTS and DECISIONS are unchanged, no game was written, and the DR-82 correction is a genuine byte-exact append (the 44,184 bytes of the pre-batch revision are a byte-exact prefix of the 46,014-byte file) whose pin reddens when the heading or the original claim is tampered with.  (4) The new tests run through run_battery -> the real Orchestrator + godot_adapter with only the MCP transport replaced; the census is 446 -> 451 test functions with one disclosed rename and no other removal; and I reproduced the gate.  (5) Every guard holds: frozen hashes unchanged, engine tree clean, no new dependency, pure LF in the changed files, nothing pushed, machine block parses and round-trips.  The two majors are: DR84A-1, the new append-only pin does NOT seal the DR-82 report's frozen prefix (I proved it green under two different in-place edits), while the report's section 6 bullet 3 says the guard checks the 44,184-byte identity; and DR84A-2, the claim that the jump window 'consumes neither coins nor ground' is unsupported for coins - the jump moves the player vertically before the coin-observing window and neither a constant, a test, nor the fixture covers a coin reachable only by that vertical move.",
  "criteria": [
    {
      "id": "A1-ORDERING",
      "title": "the headline: the jump runs before every ground-consuming step, the rule is a named constant, the coin rule is untouched, and what the frozen evidence does and does not establish",
      "pass": true,
      "evidence": [
        "src/adapter/godot.rs:679-682 runs the driving steps in the order step_input_jump, step_interaction_evidence, step_input_channel_probe, step_input_replay - the jump is first",
        "src/adapter/godot.rs:4372 INPUT_JUMP_STEP_ID = \"input_jump\"; :4390 GROUND_NEEDING_BATTERY_STEP = INPUT_JUMP_STEP_ID; :4391-4395 GROUND_CONSUMING_BATTERY_STEPS = [COIN_OBSERVING_BATTERY_STEP (interaction_evidence), INPUT_PROBE_STEP_ID (input_channel_probe), INPUT_REPLAY_STEP_ID (input_replay)]",
        "the ordering test reads those constants off the battery's own record order (tests/evidence_battery.rs:4849-4878: `.position(|id| *id == GROUND_NEEDING_BATTERY_STEP)` and `for consuming in GROUND_CONSUMING_BATTERY_STEPS`), so the DR-83 literal action name is gone; the structural pin at :4891-4920 also reads the constants",
        "my own plant (scratch copy F:\\dr84acc_scratch, src/adapter/godot.rs reverted to the pre-DR-84 order with step_input_jump last): the_jump_window_is_driven_before_the_windows_that_consume_the_ground RED exit 101 at tests\\evidence_battery.rs:4870:9, a_level_whose_goal_sits_near_the_floor_edge_still_shows_a_grounded_jump_arc RED at :4787:10 (exactly the report's p1 line), a_level_whose_ground_ends_before_the_walk_still_shows_a_grounded_jump_arc RED at :4495:36, the_jump_windows_ground_probe_precedes_every_horizontal_sample_of_the_run RED at :4599:9, and the_coin_observing_window_runs_before_every_consuming_window GREEN; restore sha256 back to 884b43dc..., cmp exit 0",
        "my own plant re-encoding the rule (GROUND_NEEDING_BATTERY_STEP = INPUT_REPLAY_STEP_ID): the_ground_ordering_rule_is_a_named_list_not_a_re_encoded_literal RED at :4892:5 and the ordering test RED at :4870:9 - the declared structural pin is load-bearing",
        "the coin rule is untouched: COIN_CONSUMING_BATTERY_STEPS at src/adapter/godot.rs:4426 is not in any diff hunk between e56b712 and 930229b, run() still drives interaction_evidence before the probe and the replay, and the coin test itself is not in the diff; my ordering plant leaves it green",
        "the executable diff between e56b712 and 930229b for src/adapter/godot.rs is 13 hunks, all of them the reorder, the two wrappers, the None-channel read, the per-window release and the new named constants plus the Playbook table; no hunk touches shows_an_arc, player_is_resting_on_ground, JUMP_GROUND_EPSILON or jump_reading",
        "frozen evidence, my own extraction from runs/smoke-t15/iter-1/candidate/.hoh/deterministic/raw/: input_replay call 7 (move_right, 60 frames) x 3411.3544921875 -> 3627.69262695312 with y already monotone from the first frame (y_first 263.925201416016, min at index 0), call 31 (jump, 30 frames) x constant 3690.02734375 and y 1492.81433105469 -> ... with min at index 0 and rise 0.0; input_channel_probe call 6 x 3283.01831054688 -> 3389.35400390625 with y constant 263.925201416016; interaction_evidence's 14 batches run x 67.3333358764648 -> 3257.35107421875 with y constant 263.925201416016",
        "the frozen level (runs/smoke-t15/iter-1/candidate/scenes/main.tscn and scripts/main.gd): Ground at (1700,300) with a 3400x40 RectangleShape2D means x in [0,3400] and a top surface at y = 280; the player's 24x32 box means the last supported centre is x = 3412; Player.position = (60, 240) and main.gd's SPAWN = (60, 240), while the resting y the whole frozen round measured is 263.925201416016",
        "with the reorder the probe is therefore taken at x = 60, deep inside the floor - and at y = 240, 23.925201416016 px ABOVE the floor's resting height, because the level itself spawns the player in the air.  Under player.gd's gravity (1400, jump only when is_on_floor()) the player needs sqrt(2*23.925/1400) = 0.185 s, about 11.1 frames at 60 Hz, before it lands; the probe reads exactly JUMP_GROUND_PROBE_FRAMES = 2 frames",
        "the frozen artifacts do not record how many physics frames elapse between the scene going live and the jump step's probe, so they do not settle whether the player is resting at that instant.  What they do show is that the interaction step's own first sample (x = 67.3333358764648 = 60 + ~2 frames of move_right, y already exactly 263.925201416016) was taken after the player had landed - but that instant is later than the jump probe's (the jump step runs before the interaction step and its probe precedes the injection preamble).  The fixture cannot resolve it either: FixtureChannel's Ledge probe decides `resting` from x alone (`x <= ledge_x`, tests/evidence_battery.rs:575-602) and answers y = 283.0 for every frame, so no test in the suite models an unsettled spawn",
        "if the player were not resting at that instant the harness still reports honestly: src/adapter/godot.rs:2472-2482 records JUMP_NOT_DRIVEN and sets ok = false when the probe says !resting, :2511 makes airborne_before_jump skip the injection entirely, :2520/:2573 push the action into held_in_game only when the injection was accepted, :2522-2524/:2575-2577 set jump_driven only for an accepted jump injection, and :2668 writes a jump_reading only when jump_driven - so no arc can be scored for an undriven window",
        "plainly, can a real round still find the jump undriven or driven in mid-air: YES.  Three shapes keep the jump undriven, all honest JUMP_NOT_DRIVEN with no reading: (i) the level spawns the player unsupported or still falling, which the frozen smoke-t15 level does by 23.925 px unless ~11 frames elapse before the probe; (ii) the engine answers the two-frame sample with a moving y for float-noisy or physics-tick reasons; (iii) the channel refuses the jump injection before the probe has classified it.  One shape still allows a mid-air drive: the two-frame flat-y proxy can certify a player who is not on a floor (an apex, a moving platform, or a level whose player script is not the frozen one) - unchanged by this batch, and now the only source of an apex inside the battery, since the battery drives no earlier jump",
        "what a real round must show to confirm the fix: a battery record order with input_jump before interaction_evidence, input_channel_probe and input_replay; an input_jump.json carrying a jump:ground_probe call (frame_count 2, two samples whose y agree within JUMP_GROUND_EPSILON) that precedes any jump injection; a jump:play_input_recording accepted inside the game process with no refusal; a jump_reading with rise > 0, monotone_fall = false, shows_an_arc = true and verdict JUMP_ARC_OBSERVED behind an injected press; the jump step's record ok = true with no JUMP_NOT_DRIVEN token; a jump:release_after_window pressed = false after the window's frame sample; and the probe's x inside the level's own last supported centre.  position:neq must stay necessary and insufficient"
      ],
      "judgement": "The ordering is real, runs in the right direction, is expressed as the named list the previous acceptance asked for, and leaves the coin rule alone.  On the frozen evidence the jump is now probed at the level's own start x - the dependency on the goal's position is gone by construction - but whether the player is resting at that instant is not established by the frozen artifacts, because the frozen level spawns the player 23.925 px above its floor and the probe is two frames long.  The report lists this as an inference and as failure shape (1), but describes it as 'a few pixels', which understates a quarter-second fall; that is DR84A-3."
    },
    {
      "id": "A2-FALSE-CONFIRMATIONS",
      "title": "the four ways a pass could be faked: which this change closes, which it leaves open",
      "pass": true,
      "evidence": [
        "an arc with no preceding ground probe: not producible.  The probe is taken inside the jump window's own iteration before the injection (src/adapter/godot.rs:2404-2485, labelled jump:ground_probe at :2451/:2462), and a jump_reading is written only for a window with jump_driven (:2668), which requires an accepted injection",
        "an injection the engine refused: not producible.  The new None-channel path (src/adapter/godot.rs:2526-2561) classifies the refusal with the engine's own -32602 code and the ACTION_NOT_BOUND marker, sets needs_p3/ok = false and skips the window, and jump_driven is set only inside the `if injected` branches (:2522, :2575); a refused jump can never carry a reading",
        "relying on the engine's position assertion alone: unchanged and still insufficient.  POSITION_ASSERT_PASSED is only ever written as a summary token (src/adapter/godot.rs:2785) - grep over src finds no reader - and the jump's pass condition is the arc rule plus movement on the intended axis (:2701-2707).  The batch added no criterion and no new reliance on the assertion",
        "a produced level whose jump ignores its own on-floor guard: still possible in principle, and unchanged.  player_is_resting_on_ground is a two-flat-frame proxy, so a player at an apex, on a moving platform, or driven by a level-specific script can be certified off the ground and then produce an arc.  My plant making the predicate return true unconditionally reddens a_level_with_no_usable_ground_reports_the_jump_unobserved at tests\\evidence_battery.rs:4687:5, so the predicate is load-bearing - but the proxy itself is the residual shape",
        "what the batch removes: the apex the battery itself used to supply.  Before DR-84 the jump window was driven inside the same pass as the horizontal windows, after a drive; now no earlier battery step jumps, so the 'two flat frames at the apex of the battery's own previous jump' shape cannot occur.  What remains is a level-shaped apex/moving-platform risk, which the previous acceptance already listed and this batch neither fixes nor worsens",
        "the one shape the batch could introduce is a false NEGATIVE, not a false positive: an unsettled or unsupported spawn is now refused (JUMP_NOT_DRIVEN) where the old order let the player settle during a long drive; the failure direction is closed, which is the discipline this criterion wants"
      ],
      "judgement": "Three of the four false-confirmation shapes are closed by the code paths this batch added or by the arc gate that was already there, and my own probe-weakening plant confirms the gate is load-bearing.  The fourth is a pre-existing property of the two-frame proxy and remains possible; the batch reduces its surface (no battery-driven apex) and discloses the proxy as brittle.  No shape this batch adds is a false positive."
    },
    {
      "id": "A3-UNCHANGED",
      "title": "what was not changed: the arc rule, the fail-closed probe, the criteria, the frozen product requirements, any game, and the append-only correction",
      "pass": true,
      "evidence": [
        "arc rule byte-identical: JumpReading::shows_an_arc is still `self.rise > 0.0 && !self.monotone_fall` (src/adapter/godot.rs:4225-4227); a direct text extraction of the function from git show e56b712:src/adapter/godot.rs and from the delivered file compares identical, as do player_is_resting_on_ground, jump_reading, jump_reading_of, JUMP_GROUND_EPSILON, JUMP_GROUND_PROBE_FRAMES, JUMP_NOT_DRIVEN and COIN_CONSUMING_BATTERY_STEPS (my rule_compare.py, outside the repository); and my plant making shows_an_arc unconditionally true reddens a_jump_window_with_no_rise_is_rejected_too at tests\\evidence_battery.rs:4371:5 - exactly the line the report publishes for its p5",
        "ground probe fail-closed byte-identical: player_is_resting_on_ground (src/adapter/godot.rs:4186-4197) still returns false for None, for fewer than two samples, and for any y that moves by more than JUMP_GROUND_EPSILON (0.001); my plant making it accept every non-empty series reddens a_level_with_no_usable_ground_reports_the_jump_unobserved at :4687:5 - exactly the report's p3 line",
        "no criterion relaxed: the criteria live in .spec/hof-rs/REQUIREMENTS.md (E1..E6, lines 110-118) and .spec/hof-rs/PRD-mario.md; REQUIREMENTS.md is byte-identical at 298a9489... and PRD-mario.md at 4c81c3a9..., the same values the report publishes; the diff contains no grading code",
        "PRD-mario.md sha256 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a, unchanged; DECISIONS.md 245befb7...a76 and Cargo.toml e0c4992b... / Cargo.lock d98fa915... all unchanged, so no dependency was added",
        "no game written by hand: an mtime walk of the whole tree finds 0 files newer than the batch boundary 1790954845 (= e56b712's own commit time, 2026-10-02 23:27:25 +0800) under runs/** (7117 files walked; newest runs/smoke-t15/evidence/COPY_MANIFEST.txt 2026-10-02 14:54:52) and 0 under .workspace/** (743 walked; newest .workspace/fresh-t15/.godot/.gdignore 15:14:59), both exactly the report's readings and both pre-existing",
        "the DR-82 correction is a pure append: the pre-batch revision is 44,184 bytes with sha256 319397fdb369ea95c63e2eac7d4eaacd25b7825e73313e9afe863f5eb1a8e406, and it is a byte-exact PREFIX of the current 46,014-byte file (cur[:44184] == pre); the correction heading begins at offset 44,185, owns a whole line, and occurs exactly once; the appended region is 1,829 bytes (my append_check.py, all outside the repository)",
        "the appended correction is marked and the original is kept: the heading is `# 附：DR-84 更正`... and the original claim line `\"names_as_keys_per_file\": 16,` is still readable above it (line 86); the pin test asserts exactly that (`text[..offset].contains(\"names_as_keys_per_file\")`, tests/append_only_guard.rs:468-471)",
        "the pin test exists and is not vacuous: tests/append_only_guard.rs:451-472; my plants on a scratch copy show that editing the heading reddens it (`panicked at tests\\append_only_guard.rs:455:9`) and deleting the original claim above the heading reddens it (`:468:5`)",
        "the pin does NOT seal the frozen prefix: on the same scratch copy, changing the machine-block value 16 -> 17 inside the frozen prefix leaves it GREEN, and an unrelated prose edit inside the prefix ('逐名普查' -> '逐名统计') also leaves it GREEN.  Unlike every other seal in that file (seal_violations pins offset + length + sha256 for T13, DR73, DR81 and REQUIREMENTS), the DR-82 pin only checks the heading's whole-line-ness and three substring properties.  This is DR84A-1",
        "the appended correction's own account of its pin is accurate (append_only_guard.rs:652-654 lists exactly the four words the test requires and the whole-line heading) - the overstatement is in the report's section 6 bullet 3, not in the correction",
        "the `sidecar` token the pin requires appears in the correction only inside the sentence that quotes the pin's own requirement list; every substantive reference uses 旁路 (DR84A-4)"
      ],
      "judgement": "Everything the batch claims not to have touched is untouched, verified from byte hashes and my own plants rather than from the report.  The append is genuinely byte-exact and the original is kept and marked.  The one real gap is that the new pin does not do what the report says it does: it guards the heading and the claim, not the frozen prefix.  That is a defect in the guard and in one sentence of the report, not in the append itself."
    },
    {
      "id": "A4-TESTS-GATE",
      "title": "the tests and the gate: entry points, first reds versus pins, my ordering plant, and the reproduced suite",
      "pass": true,
      "evidence": [
        "entry points: every new test calls run_battery / run_battery_with_script (tests/evidence_battery.rs:4783, 4852, 4935, and the append guard reads the report directly), which goes through run_battery_opts (:1864-1889) and builds `hof_rs::runtime::run_loop::Orchestrator` with the real `godot_adapter` (:1811-1825) and replaces only `tools` with the FixtureChannel; the assertions read the raw documents the production adapter wrote",
        "my ordering plant required by the brief (scratch copy, step_input_jump moved to the end of the driving steps): the_jump_window_is_driven_before_the_windows_that_consume_the_ground RED exit 101 at tests\\evidence_battery.rs:4870:9 - the intended test reddens; the near-edge test RED at :4787:10 and the window-level probe test RED at :4599:9; the coin test GREEN; restore sha256 884b43dc..., SAME_BYTES True",
        "genuine first reds versus pins: the three reds I reproduced on the delivered bytes (the ordering pin's target, the near-edge test, the window-level test) are falsifiable and land on the same tests the report names; the declared pin the_ground_ordering_rule_is_a_named_list_not_a_re_encoded_literal is a pure `#[test]` over the constants (:4891-4920) and my re-encoding plant reddens it at :4892:5, so it is a structural pin exactly as declared; the self-release test is green under my ordering plant because on the fixture's default Ballistic jump mode the window is driven at any x, so it is not a grounding test - consistent with the report declaring its red only for the pre-step revision",
        "no test removed: a function census over tests/*.rs at e56b712 vs 930229b gives 446 -> 451 (+5): evidence_battery 68 -> 72 (+4) and append_only_guard 7 -> 8 (+1); the only removed name is the_input_replay_pass_clears_the_previous_steps_held_action_first and the only added name that replaces it is the_jump_window_clears_the_previous_steps_held_action_first (the disclosed rename); no other test file changed at all",
        "fmt: `cargo fmt --all --check` exit 0 on the delivered tree",
        "gate (forced rebuild, my own helper outside the repository): 61 `target/debug/.fingerprint/hof-rs-*` directories removed with Python glob + shutil.rmtree (no rm -rf), all 97 paths from `git ls-files '*.rs'` touched one literal path at a time (no shell wildcard, no path built from an unexpanded variable), then `cargo test --offline`: `Compiling hof-rs v0.1.0 (F:\\moonbit-hof-rs)` on log line 1, 60 result blocks, 599 passed / 0 failed / 7 ignored, 0 FAILED and 0 panicked lines.  My helper crashed in its own post-run aggregation (int('test')) before recording the literal exit code - my bug, disclosed; cargo's exit is 0 for a run whose compilation finished and every one of whose 60 binaries reported 'test result: ok' with 0 failed.  The listing run confirms it: `cargo test --offline -- --list` exit 0 with 606 `: test` lines, 60 per-binary summaries summing to 606, and `-- --list --ignored` exit 0 naming exactly the seven e0..e6 tests, so 606 - 7 = 599",
        "the report's own gate log is a single complete run: C:\\Users\\wyl\\AppData\\Local\\Temp\\dr84\\gate_run.log has `Compiling hof-rs v0.1.0 (F:\\moonbit-hof-rs)` on line 1, `Finished ... in 55.35s`, 60 result blocks summing to 599 passed / 0 failed / 7 ignored and `EXIT=0`, with 0 FAILED/panicked lines - so there is no interruption to weigh this time, and build identity is checkable inside one log; final_run1.log is a second complete run with its own Compiling line (599/0/7), and baseline_run.log the pre-batch 594/0/7",
        "the published changed-file hashes match the bytes on disk (godot.rs 884b43dc..., evidence_battery.rs 5d5d0c11..., append_only_guard.rs 1557ef8d..., TASK-DR82-REPORT.md ee88185...), so the gate and the published revision are the same revision"
      ],
      "judgement": "The tests exercise the real adapter and read its raw output; my ordering plant reddens the intended ordering test and the two grounding tests while leaving the coin rule green; the structural pin is load-bearing; the census shows five new functions and one disclosed rename with no silent removal; and the suite reproduces green under a forced rebuild.  The implementer's `reds_before_dr84.txt` artifact, however, holds no reds at all (all GREEN, and none of the five new test names) - DR84A-7."
    },
    {
      "id": "A5-GUARDS",
      "title": "forbidden zones, frozen files, engine tree, dependencies, line endings, push state, and the machine block",
      "pass": true,
      "evidence": [
        "runs/** and .workspace/**: 0 files newer than the boundary under my own os.walk (7117 and 743 files walked, newest exactly the report's two) - I did not write a byte there and the batch did not either",
        "frozen: PRD-mario.md 4c81c3a9..., DECISIONS.md 245befb7..., REQUIREMENTS.md 298a9489..., Cargo.toml e0c4992b..., Cargo.lock d98fa915... - all byte-identical to the values the report publishes, so no dependency was added",
        "engine: godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe 194,216,960 B sha256 08483088...e9e6a, nested repo HEAD fc63af77c33368c4a1bb839c95d19750554f63a3 with an empty `git status --porcelain`; no godot-mcp path in the diff",
        "line endings: all four changed files are CR = 0 / CRLF = 0 (pure LF) and their sha256 equal the published values; the DR-84 commit touches exactly five paths (the four plus its own report)",
        "nothing staged, committed or pushed by me; HEAD = 930229bba7cfffb9a5e3964dd36536bd477fb39e (local commit fix(dr84)...) while origin/master is still e56b712da0cbd8f7c4fe3a83bfaaec24315320ae, and .git/hoh-accepted-commits.txt has no entry for 930229b - so nothing was pushed and the commit is not acceptance-marked",
        "machine block: exactly one ```json fence in the report; it parses (15 top-level keys), json.dumps(json.loads(fence), ensure_ascii=False, indent=2) reproduces the fence byte-for-byte, and the out-of-repo file machine_block_dr84.json parses to an equal object - though that file is CRLF while the fence is LF, so they are not byte-identical (DR84A-6)",
        "my own writes were confined to C:\\Users\\wyl\\AppData\\Local\\Temp\\dr84acc (helpers and logs) and F:\\dr84acc_scratch (a copy outside the repository); the only repository write is this acceptance file, plus the pre-existing byte-identical sidecar rewrite that tests/round_artifacts_sidecar.rs performs on every cargo test (git status shows no diff for it)",
        "residual-risk list adjudicated: the 'measured' items are measured as claimed (I reproduced the frozen readings, the plant reds at the published lines, the census and the gate); the 'inferred' items are correctly labelled, and the central one - that is_on_floor() holds at the position the level spawns the player at - is exactly what a real round must test; the report's 'unverified' list of three shapes a real round could still fail is honest, though it omits the coin-hazard shape of DR84A-2 and understates the unsettled-spawn one as 'a few pixels' (DR84A-3)"
      ],
      "judgement": "Every guard holds under my own instruments: nothing under runs/** or .workspace/**, every frozen hash unchanged, the engine tree clean, no new dependency, pure LF, nothing pushed.  The machine block parses and round-trips; the only gap is that the out-of-repo copy is CRLF, which the report's 'compared byte-for-byte' phrasing glosses."
    }
  ],
  "plants": [
    {
      "id": "mine-1",
      "where": "F:\\dr84acc_scratch\\src\\adapter\\godot.rs",
      "plant": "move self.step_input_jump().await? to the end of run()'s driving steps (the pre-DR-84 order)",
      "result": "the_jump_window_is_driven_before_the_windows_that_consume_the_ground RED exit 101 tests\\evidence_battery.rs:4870:9; a_level_whose_goal_sits_near_the_floor_edge_still_shows_a_grounded_jump_arc RED :4787:10; the_jump_windows_ground_probe_precedes_every_horizontal_sample_of_the_run RED :4599:9; a_level_whose_ground_ends_before_the_walk_still_shows_a_grounded_jump_arc RED :4495:36; the_coin_observing_window_runs_before_every_consuming_window GREEN",
      "restore": "sha256 back to 884b43dc..., cmp exit 0, bytes identical"
    },
    {
      "id": "mine-2",
      "where": "scratch src/adapter/godot.rs",
      "plant": "GROUND_NEEDING_BATTERY_STEP = INPUT_REPLAY_STEP_ID (the report's p4)",
      "result": "the_ground_ordering_rule_is_a_named_list_not_a_re_encoded_literal RED :4892:5; the ordering test RED :4870:9",
      "restore": "byte-exact"
    },
    {
      "id": "mine-3",
      "where": "scratch src/adapter/godot.rs",
      "plant": "player_is_resting_on_ground returns true for every non-empty series (the report's p3, fail open)",
      "result": "a_level_with_no_usable_ground_reports_the_jump_unobserved RED :4687:5",
      "restore": "byte-exact"
    },
    {
      "id": "mine-4",
      "where": "scratch src/adapter/godot.rs",
      "plant": "shows_an_arc unconditionally true (the report's p5)",
      "result": "a_jump_window_with_no_rise_is_rejected_too RED :4371:5",
      "restore": "byte-exact"
    },
    {
      "id": "mine-5",
      "where": "F:\\dr84acc_scratch\\.spec\\hof-rs\\tasks\\TASK-DR82-REPORT.md",
      "plant": "in-place edit INSIDE the frozen prefix: machine-block value 16 -> 17",
      "result": "the_dr82_census_claim_carries_its_dr84_qualifier GREEN - the prefix is not sealed (DR84A-1)",
      "restore": "byte-exact"
    },
    {
      "id": "mine-6",
      "where": "scratch TASK-DR82-REPORT.md",
      "plant": "in-place prose edit inside the frozen prefix",
      "result": "GREEN - same finding",
      "restore": "byte-exact"
    },
    {
      "id": "mine-7",
      "where": "scratch TASK-DR82-REPORT.md",
      "plant": "edit the DR-84 correction heading",
      "result": "RED, panicked at tests\\append_only_guard.rs:455:9",
      "restore": "byte-exact"
    },
    {
      "id": "mine-8",
      "where": "scratch TASK-DR82-REPORT.md",
      "plant": "delete the original names_as_keys_per_file line above the heading",
      "result": "RED, panicked at tests\\append_only_guard.rs:468:5",
      "restore": "byte-exact"
    }
  ],
  "defects": [
    {
      "id": "DR84A-1",
      "severity": "major",
      "what": "The append-only guard added for TASK-DR82-REPORT.md does not seal the report's frozen prefix.  tests/append_only_guard.rs:451-472 only checks that the correction heading owns a whole line, that the correction contains four substrings, and that the original claim is still readable above the heading; unlike every other document in that file it never calls seal_violations, so no pinned length or sha256 is compared.  The report's section 6 bullet 3 says the 44,184 bytes are byte-identical to the reviewed revision 'which the new guard test checks by whole-line offset' - the guard does not check that identity, only the heading's position.  The machine block's items.dr82_prose_correction.test describes the weaker property accurately, so the correction itself is honest and the append really is byte-exact; the gap is the guard and the one sentence that overstates it.",
      "reproduction": "On the scratch copy F:\\dr84acc_scratch: replace `\"names_as_keys_per_file\": 16,` with `...: 17,` in the frozen prefix and run `cargo test --offline --test append_only_guard -- --exact the_dr82_census_claim_carries_its_dr84_qualifier` - it is GREEN (the file change is inside the machine-readable block, before the heading).  An unrelated prose edit in the prefix is GREEN too.  Editing the heading gives RED at tests\\append_only_guard.rs:455:9 and deleting the original claim line gives RED at :468:5, so the pin is non-vacuous but incomplete.  On the real report, the prefix really is intact: cur[:44184] == the e56b712 revision (sha256 319397fd...), so this is a guard gap, not a tampering."
    },
    {
      "id": "DR84A-2",
      "severity": "major",
      "what": "The claim that the reorder is safe for the coin criterion ('the jump window drives only `jump`, so it consumes neither coins nor ground', src/adapter/godot.rs:678 and report section 1) is not established.  The jump window now runs BEFORE the coin-observing window (interaction_evidence) and it moves the player vertically: the frozen player.gd applies jump_velocity = -430 with gravity 1400, an apex of about 66 px, and coin.gd collects a coin on body_entered from a node in the 'player' group.  A level that places a coin above its spawn, reachable only by that jump, would have the coin collected before interaction_evidence reads the counter for the first time, so the 0 -> 1 transition F10 needs would be unobservable - the same class of false negative DR-78 created the coin rule to prevent.  Nothing covers this: COIN_CONSUMING_BATTERY_STEPS names only input_channel_probe and input_replay (src/adapter/godot.rs:4426), the ordering test only reads that list, and the fixture's counter is a function of the horizontal interaction drive (tests/evidence_battery.rs:790 `format!(\"Coins: {}\", self.interactions())`), so no test can express a coin collected by a vertical jump.",
      "reproduction": "Read src/adapter/godot.rs:676-682 (the jump runs before interaction_evidence), :2206-2214 (the jump step) and the frozen runs/smoke-t15/iter-1/candidate/scripts/player.gd (jump_velocity -430, gravity 1400, `is_on_floor()` guard) and coin.gd (body_entered -> collect via the player group).  Arithmetic from those frozen constants: standing at the spawn the player's box spans y 247.925..279.925; the jump's apex is 430^2/(2*1400) = 66.04 px higher, so at the apex the box spans 181.88..213.88 - and a coin at (60, 200), whose Area2D carries the default 20x20 RectangleShape2D, spans y 190..210 at the same x.  Such a coin is collected by the jump and never by the rightward interaction drive, which starts at x = 60 and only moves right.  The frozen smoke-t15 level does not have such a coin (Coin1 is at x = 200), so this is a counterexample constructed from the frozen scripts, not a measured round; no engine ran."
    },
    {
      "id": "DR84A-3",
      "severity": "minor",
      "what": "The report's framing of the unsettled-spawn risk understates the frozen level.  Section 8 shape (1) and residual_risks.inferred say a level that spawns the player 'a few pixels above its floor' would now be refused where the old order let it settle.  The frozen smoke-t15 level spawns the player at (60, 240) while the resting y the whole round measured is 263.925201416016 - a 23.925 px drop, about 0.185 s or 11.1 frames of fall - against a two-frame probe.  Whether the player is resting when the jump is now probed is therefore genuinely undetermined by the frozen artifacts, and the report's central inference ('is_on_floor() holds at the position the level spawns the player at') is not supported by them.",
      "reproduction": "runs/smoke-t15/iter-1/candidate/scenes/main.tscn (Player position = Vector2(60, 240), Ground at (1700,300) with a 3400x40 shape so the top surface is y = 280) and scripts/main.gd (const SPAWN := Vector2(60, 240)); the resting y 263.925201416016 is what every frozen interaction/probe sample reads, so the drop is 23.925201416016 px.  Fall time from player.gd's gravity 1400: t = sqrt(2*23.925201416016/1400) = 0.1849 s, about 11.1 physics frames at 60 Hz, against a two-frame probe."
    },
    {
      "id": "DR84A-4",
      "severity": "info",
      "what": "The guard test requires the correction to carry the literal token `sidecar`, and the correction satisfies it only inside the sentence that quotes the pin's own requirement list; every substantive reference to the still-raw sidecars uses the Chinese word 旁路.  The substance is present, but that assertion can be satisfied by quoting the requirement rather than by making the point.",
      "reproduction": "tests/append_only_guard.rs:459 requires [\"names_as_keys_per_file\", \"键计数\", \"raw=0\", \"sidecar\"]; grep -n sidecar .spec/hof-rs/tasks/TASK-DR82-REPORT.md finds it only on line 654."
    },
    {
      "id": "DR84A-5",
      "severity": "info",
      "what": "Stale head in the machine block: head and origin_master are e56b712 while the tree's HEAD is the local commit 930229b made after the report.  Same class as DR82A-5/DR83A-2, but now disclosed in the report itself by the appended section 11, which names the commit, its five files, the unchanged origin/master and the absent ledger entry.  Nothing was pushed.",
      "reproduction": "git rev-parse HEAD -> 930229bba7cfffb9a5e3964dd36536bd477fb39e; git rev-parse origin/master -> e56b712...; git status --porcelain -> ` M .spec/hof-rs/tasks/TASK-DR84-REPORT.md` plus the four pre-existing scratch files; the report's section 11 (lines 514-531) says the same."
    },
    {
      "id": "DR84A-6",
      "severity": "info",
      "what": "The out-of-repository machine_block_dr84.json that the report names as the block's first landing point is CRLF (20,972 B) while the report's fence is LF (20,745 B).  They parse to equal objects and the in-memory round trip holds, but they are not byte-identical, so 'compared byte-for-byte' is true only of the string round trip, not of file versus fence (the DR-83 report's stronger 'byte-identical to the out-of-repo file' wording does not hold here).",
      "reproduction": "python: json.loads(fence) == json.loads(open(machine_block_dr84.json)) is True; the first differing byte is at offset 1 ('\\n' vs '\\r\\n'); sha256 fence 2abb636e..., file 6086850a...."
    },
    {
      "id": "DR84A-7",
      "severity": "info",
      "what": "The first-red artifact is not preserved.  The report says the pre-fix reds were captured and later overwritten; the file that remains, C:\\Users\\wyl\\AppData\\Local\\Temp\\dr84\\reds_before_dr84.txt, contains no RED at all (all GREEN) and none of the five new test names - it is a stale list from an earlier revision.  The claim itself is disclosed, and the mechanism is re-demonstrated by the plants on the final bytes, but no artifact supports 'genuine first red' directly.",
      "reproduction": "read C:\\Users\\wyl\\AppData\\Local\\Temp\\dr84\\reds_before_dr84.txt (33 lines, every entry GREEN, names from an earlier batch) and compare with reds.py's five DR-84 test names."
    }
  ],
  "risks": [
    "Unmeasured engine-side: nothing here shows that is_on_floor() holds at the instant the jump is now probed, that the game-process release of `jump` does not disturb real physics, or that the probe is taken early enough for the frozen level's 23.925 px spawn drop to have completed.",
    "DR84A-2: the jump step can move the player vertically before the coin-observing window; a level with a coin reachable only by a jump from near the spawn would break F10's 0 -> 1 observation, and no constant, test or fixture models it.",
    "The two-frame flat-y ground proxy is unchanged: an apex on a moving platform or a level-specific player script can still be certified as 'resting', so a mid-air jump can still be scored (a pre-existing shape the batch narrows but does not close).",
    "DR84A-1: append-only discipline for TASK-DR82-REPORT.md is not mechanically enforced; an in-place edit of its frozen prefix passes the gate.",
    "The frozen smoke-t15 sidecars runs/smoke-t15/iter-1/traj/*.redacted.json still carry raw HOH_* values behind their keys - the correction names this as an accepted leftover, not something the batch repaired.",
    "The test suite takes about 22 minutes (the implementer's gate log sums 1339.69 s of per-binary wall time, with one binary at 434.45 s); any batch that runs it in one foreground command can still trip a ten-minute executor cap, so 'the whole suite ran in one command' is a statement about how it was invoked (background), not about it being fast.",
    "The fixture's Ledge physics is a step function of x, not physics; the tests prove the drive order, not any real cliff.",
    "tests/round_artifacts_sidecar.rs rewrites one tracked sidecar under .spec on every cargo test, byte-identically; my required gate run performed that rewrite (git status shows no diff for it)."
  ],
  "unverified": [
    "Everything engine-side: the probe at the spawn, the reorder, the per-window release and the None-channel classification have never run against a live game process in this acceptance.",
    "Whether a real round now shows a grounded jump on the frozen level, or an honest JUMP_NOT_DRIVEN because the 23.925 px spawn drop had not finished - the frozen artifacts do not record the elapsed physics frames at that instant.",
    "The implementer's pre-implementation first-red line numbers: they cannot be re-derived from the delivered bytes (the constants had to exist for the tests to compile), and the artifact named for them holds no reds; what I could show is that the same tests are falsifiable and red on the final bytes.",
    "The implementer's five plants as they ran them: I reproduced p3, p4 and p5 at their published lines and an ordering plant of my own, but not their p1/p2 byte-for-byte, and not their exact restore of the reviewed tree (mine were on a scratch copy).",
    "The four 60-second-plus tests and the 434 s binary: I observed the suite's slowness myself in a killed warm run, but I did not profile which tests dominate.",
    "I did not line-by-line audit all 232 changed lines of src/adapter/godot.rs or all 442 of tests/evidence_battery.rs; I audited the diff, the changed call paths, the constants, the fixtures and everything the tests exercise."
  ],
  "what_i_did_not_check": [
    "Did not start, stop or inspect any engine process; ran no round; made no network call.",
    "Did not write anything under runs/**; did not modify any workspace directory, any existing report, the frozen specification, DECISIONS.md or godot-mcp/**.  The only repository writes were the pre-existing byte-identical sidecar rewrite that the test suite performs and this acceptance file.",
    "Used no rm -rf (fingerprints were removed with Python glob + shutil.rmtree), built no path from an unexpanded shell variable, and never used git checkout to restore a file.",
    "Did not stage, commit or push anything.",
    "All tampering was confined to F:\\dr84acc_scratch (a copy outside the repository) and to helper scripts under C:\\Users\\wyl\\AppData\\Local\\Temp\\dr84acc; every scratch source was restored byte-exactly with sha256 and cmp after each plant.",
    "Worked alone; delegated nothing.",
    "The forced-rebuild gate touched the mtime of the 97 tracked .rs paths (the run the brief requires); no content changed and the changed files' sha256 are the published ones."
  ],
  "advice_for_the_next_batch": [
    "Seal the DR-82 report properly: add DR82_PRE_DR84_BYTES (44,184) and DR82_PRE_DR84_SHA256 (319397fd...) and route the pin through seal_violations, exactly as T13/DR73/DR81/REQUIREMENTS are sealed, and reword section 6 bullet 3 so it says what the guard checks.",
    "Decide the coin question the reorder opens: either add the jump step to a coin-consumer list (and test it), or place the coin-observing window before the jump, or record the hazard explicitly as an accepted limitation - it is currently asserted away by a sentence that is not true in general.",
    "On hardware, confirm the grounding at the instant the jump is probed: the raw input_jump.json must show a two-frame jump:ground_probe with flat y before any injection, and the probe's x must be inside the level's own last supported centre; if the probe reads a moving y on the frozen level, that is the 23.925 px spawn drop, and the honest JUMP_NOT_DRIVEN means E3 is still unmet - do not read the reorder as closing it.",
    "Stop calling the first-red set 'genuine' unless the red artifact is preserved; keep the pre-implementation log under a name that is not overwritten, or declare the tests as pins (the DR-83 acceptance's own standard).",
    "Make the out-of-repo block file LF (or say 'the parsed object round-trips' instead of 'byte-for-byte') so the machine-block claim is exactly true.",
    "Record every full-suite log a batch writes, and note that the suite takes about 22 minutes, so the gate must be run as a background job rather than as one capped foreground command."
  ]
}
```

## 0. What this file is

Independent acceptance of the **TASK-DR84** offline batch, written by a fresh subagent with no
upstream conversation context.  Everything below was produced here: the readings of the frozen
`runs/smoke-t15` artifacts, the code reading, the plants, the census and the gate.  The reviewed
report `.spec/hof-rs/tasks/TASK-DR84-REPORT.md` (46,327 B, sha256 `31fb5510...`) was read as a lead,
never as evidence.  The machine-readable block above was produced with
`json.dumps(..., ensure_ascii=False, indent=2)`, written first to
`C:\Users\wyl\AppData\Local\Temp\dr84acc\verdict_block_dr84a.json` (outside the repository),
parsed back with `json.loads`, re-serialised and compared byte-for-byte before this file was written.

**Verdict: `pass`**, with two majors.  No product behaviour this batch promises is wrong, the
ordering is real and pinned by the named list the previous acceptance asked for, the append is a
genuine byte-exact append, and every guard holds.  But (DR84A-1) the new append-only pin does not
seal the report's frozen prefix although the report says it does, and (DR84A-2) the reorder is
asserted to be coin-safe on a sentence that is not true in general - a vertical jump can collect a
coin before the observing window reads the counter.  Neither invalidates the headline; both should be
cleared before the next batch treats the append-only gap or the coin criterion as safe.

## 1. Item-by-item table

| # | item | what I verified myself | result |
|---|---|---|---|
| 1 | **the ordering (headline)** | `src/adapter/godot.rs:679-682` drives `input_jump` before `interaction_evidence`, `input_channel_probe`, `input_replay`; `:4390-4395` names the rule as `GROUND_NEEDING_BATTERY_STEP` / `GROUND_CONSUMING_BATTERY_STEPS`; the pin at `tests/evidence_battery.rs:4849-4878` reads those constants, not a literal action name; `COIN_CONSUMING_BATTERY_STEPS` and the coin test are untouched and stay green under my ordering plant | **pass** |
| 1b | **would the player be on the ground when the jump is driven** | on the frozen level the jump is now probed at the spawn `x = 60`, inside the floor `[0,3400]` - but at `y = 240`, **23.925 px above** the resting `y = 263.925201416016`, so the level itself starts the player in the air and the two-frame probe needs ~11.1 frames (0.185 s) of settling.  The frozen artifacts do not record the elapsed frames, and the fixture decides `resting` from `x` alone, so **undetermined offline** | **pass, limit named** |
| 1c | **honesty if not on the ground** | `:2472-2482` records `JUMP_NOT_DRIVEN` and fails the step; `:2511` skips the injection; `:2668` writes a reading only when `jump_driven`, which requires an accepted injection.  A real round could still find the jump undriven in three shapes; all three fail closed | **pass** |
| 1d | **what a real round must show** | battery order `input_jump` first; a `jump:ground_probe` (2 flat-`y` samples) before any injection whose `x` is inside the level's own last supported centre; an accepted in-game injection; `jump_reading` with `shows_an_arc = true`, `rise > 0`, `monotone_fall = false`, verdict `JUMP_ARC_OBSERVED`; step `ok = true` with no `JUMP_NOT_DRIVEN`; a `jump:release_after_window` release; `position:neq` necessary and insufficient | **named** |
| 2 | **the false confirmations** | arc-without-probe, refused injection and assertion-alone are closed by the code paths I read and by the arc gate (my fail-open plant reddens at `:4687:5`); the level-that-ignores-its-own-guard shape **remains possible** through the two-frame flat-`y` proxy (apex/moving platform), though the battery no longer supplies the apex itself | **pass** |
| 3 | **what was not changed** | `shows_an_arc` and `player_is_resting_on_ground` are byte-identical (my plants redden at the published `:4371:5` and `:4687:5`); REQUIREMENTS `298a9489...` and PRD `4c81c3a9...` unchanged; 0 files newer than the boundary under `runs/**` (7117 walked) and `.workspace/**` (743); the 44,184-byte pre-batch revision is a byte-exact prefix of the 46,014-byte report | **pass** |
| 3b | **the append-only pin** | heading edit -> RED `:455:9`; deleting the original claim -> RED `:468:5`; **in-place edit of a value or of prose inside the frozen prefix -> GREEN** - the prefix is not sealed (DR84A-1); `sidecar` is satisfied only by the correction's own quotation of the requirement (DR84A-4) | **defect (major)** |
| 4 | **the tests and the gate** | all new tests go through `run_battery` -> the real `Orchestrator` + `godot_adapter` with only `tools` replaced; my ordering plant reddens the intended ordering test at `:4870:9`; census 446 -> 451 with one disclosed rename and no silent removal; `cargo fmt --all --check` exit 0; forced rebuild 61 fingerprints removed / 97 tracked `.rs` paths touched - **599 passed / 0 failed / 7 ignored**, 60 blocks, exit 0, `Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)` on line 1 | **pass** |
| 5 | **guards** | frozen hashes, engine tree (`08483088...`, nested repo clean at `fc63af77...`), no new dependency, pure LF, nothing staged/pushed (`HEAD = 930229b`, `origin/master = e56b712`, no ledger entry); `runs/**` and `.workspace/**` untouched; machine block parses and round-trips; the out-of-repo file is CRLF vs the fence's LF (DR84A-6) | **pass** |

## 2. Plants I produced myself

All tampering happened in `F:\dr84acc_scratch` (a copy outside the repository, byte-refreshed from
the delivered tree) or in helper scripts under `C:\Users\wyl\AppData\Local\Temp\dr84acc`; the
reviewed tree was never written, and every scratch source was restored from a byte backup and
hash-verified after each plant.

| # | plant (on the copy) | intended test | observed |
|---|---|---|---|
| mine-1 | move `step_input_jump` to the **end** of `run()`'s driving steps | `the_jump_window_is_driven_before_the_windows_that_consume_the_ground` | **RED** exit 101 `tests\evidence_battery.rs:4870:9` - the intended test reddens |
| mine-1 | same | near-edge / window-level / ground-ends-before-walk tests | RED at `:4787:10`, `:4599:9`, `:4495:36`; the coin test **GREEN** |
| mine-2 | `GROUND_NEEDING_BATTERY_STEP = INPUT_REPLAY_STEP_ID` | `the_ground_ordering_rule_is_a_named_list_not_a_re_encoded_literal` | **RED** `:4892:5`; ordering test also RED `:4870:9` |
| mine-3 | `player_is_resting_on_ground` accepts everything | `a_level_with_no_usable_ground_reports_the_jump_unobserved` | **RED** `:4687:5` |
| mine-4 | `shows_an_arc` unconditionally true | `a_jump_window_with_no_rise_is_rejected_too` | **RED** `:4371:5` |
| mine-5 | in-place edit inside the DR-82 report's frozen prefix (16 -> 17) | `the_dr82_census_claim_carries_its_dr84_qualifier` | **GREEN** - the prefix is not sealed |
| mine-6 | unrelated prose edit inside the same prefix | same | **GREEN** |
| mine-7 | edit the correction heading | same | **RED** `append_only_guard.rs:455:9` |
| mine-8 | delete the original claim above the heading | same | **RED** `append_only_guard.rs:468:5` |

Counterexamples I checked rather than assumed: the frozen jump window really is a monotone free fall
at `x = 3690.03` (my own extraction of `raw/input_replay.json`); the frozen player really does spawn
at `y = 240` while resting at `263.925` (`main.tscn` + `main.gd`); `POSITION_ASSERT_PASSED` really has
no reader in `src`; and the coin fixture really cannot express a vertical pickup, because its counter
is `format!("Coins: {}", self.interactions())`.

## 3. Independent judgement

**The headline is the right fix and it is now the right shape.** The previous acceptance asked for the
rule to be a named constant list rather than a literal action name, and for the jump to run before the
windows that consume the ground; both are done.  The executable diff is small and contains no level
measurement: a reorder in `run()`, two thin wrappers over one shared pass, two named constants, the
per-window release, and the `None`-channel classification that keeps an unreadable channel honest.  I
checked the rule's direction with my own plant, and I checked that it does not disturb the coin rule
by watching the coin test stay green while the ordering test reddened.

**On the frozen evidence the fix removes the dependency it was meant to remove, and reveals a new
question.** The drive can no longer carry the player past the goal before the jump, because the jump
now runs first.  But the frozen level starts the player 23.925 px above its floor, so "the jump is
probed where the level starts the player" is now a statement about `x`, not about `y` - and whether the
two-frame probe sees a resting player depends on physics frames the artifacts do not record.  The
report labels this as an inference and as a failure shape, which is honest; calling it "a few pixels"
is not, and that is DR84A-3.  The harness fails closed either way, which is the property that matters
most.

**Two claims are weaker than their sentences.**  The append-only pin guards a heading and three
substrings, not the frozen prefix, so an in-place edit of the DR-82 report passes the gate the report
says it added for exactly that purpose (DR84A-1).  And "the jump window drives only `jump`, so it
consumes neither coins nor ground" is true of the ground and false of coins: the window moves the
player up before the coin-observing window reads the counter, and no constant, test or fixture models
a coin reachable only by that vertical move (DR84A-2).

## 4. Unverified (with reasons)

See the `unverified` array.  The load-bearing entries are: everything engine-side; whether the frozen
level's 23.925 px spawn drop is finished when the jump is probed (the artifacts do not record elapsed
frames); the implementer's pre-implementation first-red lines (unreproducible from the delivered
bytes, and the artifact named for them holds no reds); and their exact p1/p2 restoration (I reproduced
p3/p4/p5 and my own ordering plant instead).

## 5. What I did not check

No engine, no round, no network; nothing under `runs/**` and no workspace directory touched; no
existing report, frozen specification, `DECISIONS.md` or `godot-mcp/**` modified; no `rm -rf`, no path
built from an unexpanded variable, no `git checkout` restore; nothing staged, committed or pushed.  My
only repository write is this acceptance file plus the pre-existing byte-identical sidecar rewrite
that `cargo test` performs (git status shows no diff for it).  The forced-rebuild gate touched the
mtime of 97 tracked `.rs` paths as the brief requires; their contents are unchanged.  I did not audit
all 232 changed lines of `src/adapter/godot.rs` or all 442 of `tests/evidence_battery.rs` line by
line, and I did not profile which tests dominate the ~22-minute suite.

## 6. Advice for the next batch

See `advice_for_the_next_batch` in the machine block.  In one line: seal the DR-82 prefix through
`seal_violations`, decide the coin hazard the reorder opens (add the jump to a coin-consumer list, or
observe the coin before the jump, or declare it), and on hardware verify the probe's flat `y` at the
instant the jump is now driven instead of assuming the spawn is grounded.
