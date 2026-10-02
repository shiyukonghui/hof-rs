```json
{
  "task": "TASK-DR85-ACCEPTANCE",
  "kind": "independent acceptance of the TASK-DR85 offline batch; no engine, no round, no network; nothing staged, committed or pushed by me; nothing written under runs/**",
  "task_book": "none: the batch was dispatched as a self-contained prompt (there is no .spec/hof-rs/tasks/TASK-DR85.md; verified by listing the tasks directory)",
  "reviewed_report": ".spec/hof-rs/tasks/TASK-DR85-REPORT.md",
  "reviewed_report_sha256": "21366a3fc1603645642533acd0883443134e33f5ac2e15c9ed90310ed3a6f3e4",
  "reviewed_report_note": "the sha256 is of the report's machine-readable fence content (13,608 B), which round-trips byte-for-byte through json.dumps(..., ensure_ascii=False, indent=2); the file itself is 36,725 B / 485 lines, pure LF",
  "head_at_acceptance": "5e840aade50efad38dd806c3a9e5249b655f0f79",
  "origin_master_at_acceptance": "f6ea2d1c9e82da0add93f512d25a28f06306ae3b",
  "head_note": "the report's machine block says head = f6ea2d1 and that the three changed files are uncommitted working-tree modifications; that was true when the report was written (report mtime 03:16:33).  The dispatcher then committed exactly those files (plus the report) as the local commit 5e840aa at 03:20:52, which is not pushed (origin/master is still f6ea2d1).  Every published changed-file hash equals the committed blob and the working tree byte for byte, so the reviewed revision is the committed revision",
  "pushed": false,
  "reviewed_revision": {
    "src/adapter/godot.rs": "8ff8b643d70d99c35b95165d4d6549b980f97614e780c1f42e03b14622a4f1ca",
    "tests/evidence_battery.rs": "dc14fc3802f60a4e18f6be0ffdf104e0731b0566f1dda0fa5aacef452fdbee88",
    "tests/append_only_guard.rs": "27aaf1dbcc04f079d93793cc453288e83190d3e928d11bab7cee469a228f0492",
    ".spec/hof-rs/tasks/TASK-DR82-REPORT.md": "ee88185054acaade384fd47d2c7ae164606e21f65c0dd1969efdda593fbef691"
  },
  "verdict": "pass",
  "verdict_scope": "Both majors the DR-84 acceptance opened are closed and verified under my own instruments: (1) the jump step reads the coin counter before it drives and the reading is the first call of raw/input_jump.json, strictly ahead of the press, so a coin the jump collects never has its pre-jump value destroyed; the residual (a counter that is not readable at the baseline read) is real, disclosed by the report, and reproduced by me.  (2) the DR-82 pin now goes through seal_violations and pins the reviewed 44,184-byte revision, and both plants the DR-84 acceptance used (a machine-block edit and a prefix prose edit) now RED at tests/append_only_guard.rs:313:5, where they were GREEN before.  The spawn drop is waited for within a bounded 16x2-frame cap against a measured 11.1-frame drop, both unreadable and cap-reached cases stay fail-closed, and the cap residual is stated honestly.  I reproduced all six of the batch's plants at their published lines with my own mutations (three of them byte-identical mutated hashes), reproduced the forced-rebuild gate at 602 passed / 0 failed / 7 ignored / listing 609 / exit 0, and every guard holds.  Six findings are recorded, all info or minor; none changes the deliverable.",
  "criteria": [
    {
      "id": "A1-COIN-ORDER",
      "title": "the headline: the jump step observes the coin counter before it drives and the reading precedes the injection in the raw artifact",
      "pass": true,
      "evidence": [
        "code: src/adapter/godot.rs:2219-2233 - step_input_jump calls observe_coin_counter_before_jump(scene_tree.as_ref(), &mut leading_calls) BEFORE run_replay_windows, and hands leading_calls to the pass; run_replay_windows at :2328 starts `let mut calls = leading_calls;` so the baseline calls are the first entries of raw/input_jump.json",
        "code: observe_coin_counter_before_jump (:2261-2302) enumerates `scene_tree.map(hud_label_candidates)` and reads each candidate with semantic::NODE_PROPERTIES + properties [\"text\"]; the text extraction is `value.as_str().map(ToOwned::to_owned).or_else(|| Some(value.to_string()))` and the match is `text.trim_start().starts_with(COIN_COUNTER_PREFIX)` - byte-for-byte the same reader the interaction window uses in read_hud_text (:3574-3608) and the same rule at :3140",
        "code: run() passes the SAME tree snapshot to both: :686 `self.step_input_jump(scene_tree.clone())` and :687 `self.step_interaction_evidence(scene_tree.clone())`, where scene_tree came from :642 step_play_scene().  So the candidate set of the jump baseline is the candidate set of the observing window by construction",
        "raw artifact (my own run of the real battery on the fixture's apex-coin level, dumped to C:\\Users\\wyl\\AppData\\Local\\Temp\\dr85acc\\raw_input_jump_apex.json, 13,716 B, sha256 0eae83f4...): the call list is [jump:coin_baseline x4, editor_side_injection, jump:clear_move_right, jump:clear_move_left, jump:ground_probe, jump:replay_frame_before, jump:create_input_recording, jump:play_input_recording, jump:test_scenario, jump:stop_input_recording, ...]; baseline_index=0, probe_index=7, press_index=10; the first baseline call carries `Coins: 0` in its payload; jump_reading = {rise 31.19999999999999, monotone_fall false, shows_an_arc true, verdict JUMP_ARC_OBSERVED}",
        "the four baseline calls are the four HUD Labels the frozen tree names (the counter cell plus Lives/Score/Time); the step returns on the first whose text starts with `Coins:`, exactly as the observing window does, so the candidate sets cannot diverge while the tree is the same snapshot",
        "the fixture's apex-coin mode makes the counter a function of the jump press only (`with_coin_in_the_jump_apex` + InteractionMode::NoPickupNoWin at tests/evidence_battery.rs:6209-6213; the press increments `interactions` at :1040-1052), and the test asserts observation contains the label AND `Coins: 0` (:6218-6226), baseline < press in the raw call list (:6231-6247) and the later interaction window reads `Coins: 1` (:6255-6259)"
      ]
    },
    {
      "id": "A2-COIN-RESIDUALS",
      "title": "which coins can still be counted before observed, and whether the chosen road is better than the alternatives the DR-84 acceptance offered",
      "pass": true,
      "evidence": [
        "residual 1 (baseline recorded unreadable): verified as designed.  I drove the real battery on a HUD whose counter cell reads `Collected: 0` (InteractionMode::UnreadableCounter) with my scratch-only test acc_unreadable_coin_baseline_is_recorded_not_silent: the jump step's observation carries `COIN_BASELINE_UNREADABLE`, carries no `Coins: 0`, the interaction window carries `COIN_COUNTER_UNREADABLE`, and the baseline attempt is still a labelled `jump:coin_baseline` call.  The branch is at src/adapter/godot.rs:2333-2346 (the `None =>` arm) and the unreadable token is JUMP_COIN_BASELINE_UNREADABLE",
        "residual 2 (a counter readable only AFTER the baseline read): real and reproduced.  I disabled the baseline match in my scratch copy (`starts_with(COIN_COUNTER_PREFIX)` -> a token that never matches) and ran the apex-coin level with my scratch-only test acc_residual_unreadable_baseline_loses_the_transition: the jump step says COIN_BASELINE_UNREADABLE, no `Coins: 0` appears anywhere in the step's observation, the interaction window reads `Coins: 1` BOTH before and after its drive, and it therefore reports COIN_NOT_PICKED_UP (its `text:neq` assertion is refused, src/adapter/godot.rs:3381-3388) while the jump really collected the coin.  So a coin CAN still be counted before any window observes the transition, exactly in the case the report names, and the raw artifact's only counter value is the post-jump `1`",
        "the residual's consequence is slightly worse than the report's sentence: on such a HUD the interaction window emits COIN_NOT_PICKED_UP (a verdict that the coin was not picked up) even though the jump collected it, and only the jump step's COIN_BASELINE_UNREADABLE token discloses the gap.  This is DR85A-4 (info); the report's `residual_risks.can_any_coin_still_be_counted_before_it_is_observed` states the gap but not that the later window's verdict is COIN_NOT_PICKED_UP",
        "the other route (a counter unreadable in BOTH windows) is honest: no transition is claimed by either window",
        "why the 'list the jump as a coin consumer' road is unsatisfiable, verified from the tests rather than from the report: the coin ordering test (tests/evidence_battery.rs:6049-6061) asserts `observing < index` for every member of COIN_CONSUMING_BATTERY_STEPS; the ground ordering test (:4981-4993) asserts `needing < index` for every member of GROUND_CONSUMING_BATTERY_STEPS; COIN_OBSERVING_BATTERY_STEP is `interaction_evidence` (src/adapter/godot.rs:4526) and GROUND_NEEDING_BATTERY_STEP is `input_jump` (:4563).  Adding input_jump to the coin-consumer list would demand interaction_evidence before input_jump while the ground rule demands input_jump before interaction_evidence - a contradiction, not an inelegance.  The structural pin at :5016-5025 additionally requires every coin/ground consumer to be one of the three horizontal steps, so the list cannot absorb the jump either",
        "why 'declare only' is worse: a declaration with no reading leaves the 0 -> 1 transition destroyed and asserts a property rather than preserving it - the DR84A-2 defect class itself",
        "the road chosen does not prevent the counter from changing before the observing window (nothing could, given the ordering), it records the pre-jump reading ahead of the consumption; the report's machine-block phrase 'never counted before it is observed' is stronger than the code guarantees when the baseline is unreadable, and its own residual section corrects it"
      ]
    },
    {
      "id": "A3-PREFIX-SEAL",
      "title": "the DR-82 prefix seal pins the reviewed length and hash, reddens on both plants, and is not shifted by one byte",
      "pass": true,
      "evidence": [
        "the pin is exactly the reviewed revision: bytes[..44184] of .spec/hof-rs/tasks/TASK-DR82-REPORT.md hash to 319397fdb369ea95c63e2eac7d4eaacd25b7825e73313e9afe863f5eb1a8e406 (my own sha256) and `git show 930229b^:.spec/hof-rs/tasks/TASK-DR82-REPORT.md` is 44,184 bytes with that exact sha256 - the pin is the DR-84-corrected file's own pre-correction revision from git, not a number copied out of a report",
        "boundary: byte 44183 = 0x0a (the frozen revision's final newline), byte 44184 = 0x0a (the blank separator the append starts with), byte 44185 = 0x23 ('#'), 44186 = 0x20.  DR82_DR84_SEAL is the heading WITH that leading `\\n` (tests/append_only_guard.rs:90-91) and whole_line_offset returns exactly 44184 for it (my own re-implementation of whole_line_offset agrees: seal at 44184, plain heading at 44185); the seal marker occurs exactly once in the file and the heading exactly once.  The test also asserts the two offsets explicitly (:487-498, `Ok(DR82_PRE_DR84_BYTES)` and `DR82_PRE_DR84_BYTES + 1`)",
        "the seal is not merely shifted by one byte: the pinned prefix is the 44,184-byte reviewed revision itself (hash equal above), and the appended region is the 1,830 bytes after it.  If the blank separator were deleted the marker would be found at 44183 and the seal would violate on the length check; an in-place same-length edit violates on the hash check; a length-changing edit before the marker violates on the offset check",
        "plant p4 reproduced by me (machine-readable block edit `\"names_as_keys_per_file\": 16` -> `...: 17` on a copy outside the repository): RED, exit 101, panicked at tests\\append_only_guard.rs:313:5 - and my mutated blob hash is 4bb2ce2d5f7a309b6a265d99d4c2618364aff2ac35303811193aad627906050c, byte-identical to the batch's own p4 mutation",
        "plant p5 reproduced by me (prefix prose edit `逐名普查` -> `逐名统计`): RED, exit 101, panicked at tests/append_only_guard.rs:313:5, mutated blob hash 7846e0172a0194ac1317a024c9c0087784dbe31a35a60f1414d2b05282f8b21c, byte-identical to the batch's own p5 mutation; both are GREEN under the DR-84 pin (DR84A-1, from the previous acceptance)",
        "the non-vacuity pin is falsifiable, not decorative: I neutered the seal's hash comparison in my scratch copy (`if actual != pin_sha` -> `if false && actual != pin_sha`) and `the_dr82_seal_reddens_on_a_block_edit_and_a_prose_edit` RED at tests/append_only_guard.rs:566:9 while the main DR-82 pin went GREEN - exactly the failure mode the non-vacuity test exists to catch",
        "the real report was never written: its sha256 is ee881850...46014 bytes before and after every one of my plants (the plants ran on C:\\dr85acc_scratch, an out-of-repo copy)"
      ]
    },
    {
      "id": "A4-SPAWN-DROP",
      "title": "the ground probe retries within a bounded number of attempts, the bound is justified against the measured drop, and both fail-closed directions survive",
      "pass": true,
      "evidence": [
        "the loop is bounded: src/adapter/godot.rs:2545 `'probe: while settle_attempts < JUMP_GROUND_SETTLE_ATTEMPTS {` with `settle_attempts += 1` as the first statement, so at most 16 probe calls; JUMP_GROUND_SETTLE_ATTEMPTS = 16 (:4289 area) and the per-attempt request is the same JUMP_GROUND_PROBE_FRAMES = 2, frame_interval 1",
        "my own raw-document inspection (raw_input_jump_cap.json, a level whose probe never reads a supported player): exactly 16 `jump:ground_probe` calls at indices 7..22, then no `running_game_play_input_recording` press at all, no jump_reading, and my scratch test acc_probe_cap_is_bounded_and_fail_closed asserts the extension is present ('16 probe attempt(s)') and exactly JUMP_GROUND_SETTLE_ATTEMPTS probes",
        "my own raw-document inspection (raw_input_jump_settling.json, the fixture's spawn-drop level): exactly 4 probes (indices 7..10) and the press at 13; my scratch test acc_settling_drives_on_the_landing_probe_not_the_cap asserts probes == SETTLING_PROBES_BEFORE_REST + 1 and the reading is JUMP_ARC_OBSERVED, so the window drives on the level's landing probe, not on the cap",
        "an unreadable probe is refused at once, not retried: my scratch test acc_unreadable_probe_is_refused_at_once (JumpMode::ProbeUnreadable) observes exactly ONE jump:ground_probe call, the observation carries PROBE_UNREADABLE and JUMP_NOT_DRIVEN, ok = false, and no jump_reading.  The code matches: the `(false, _)` arm breaks the loop (:2593-2600) and the Err arm breaks it (:2603-2618)",
        "the measured drop is correct: runs/smoke-t15 spawns the player at y = 240 (main.tscn / main.gd SPAWN) while the frozen round's resting y is 263.925201416016, so the drop is 23.925201416016023 px; sqrt(2*23.925201416016023/1400) = 0.18487525298356502 s = 11.092515 frames at 60 Hz (my own computation).  The cap covers 32 frames ~ 2.9x the drop, and the fixture deliberately lands after 3 probes, strictly inside the cap, with the test asserting SETTLING_PROBES_BEFORE_REST < JUMP_GROUND_SETTLE_ATTEMPTS so the cap is not the thing under test",
        "the residual is stated honestly in the report: 'a level that spawns the player unsupported, or whose drop is longer than the 16 two-frame attempts (~32 frames, ~0.53 s)' - shape (1) of can_a_real_round_still_find_the_jump_undriven, and my acc_probe_cap test confirms that shape ends in an honest JUMP_NOT_DRIVEN with no reading and ok = false",
        "the load-bearing assumption is disclosed as inferred: the wait is worth 32 frames only if a real engine advances two physics frames per repeated probe call.  The report labels that as inferred; if an engine instead re-read the same frame, a spawned-in-the-air player would read flat y and the window would be certified mid-air (a false positive, not the false negative the fix targets).  This is the main unverified risk"
      ]
    },
    {
      "id": "A5-TESTS-GATE",
      "title": "entry points, first reds versus pins, falsifiability of the three new tests, and the reproduced gate",
      "pass": true,
      "evidence": [
        "entry points: run_battery_opts builds `hof_rs::runtime::run_loop::Orchestrator` with the real GodotAdapter and replaces only `tools` with FixtureChannel (tests/evidence_battery.rs:1980-2008); the assertions read battery.json and the raw documents the production adapter wrote.  The append_only_guard test reads the report bytes directly, as its siblings do",
        "the three new tests are declared pins, not preserved first reds, exactly as the report says: `genuine_first_reds: []` in the machine block, and the report's section 4 says so in words (the DR-84 acceptance's DR84A-7 asked for that honesty)",
        "falsifiability of each new test, shown by my own plants on a copy: (1) disabling the baseline match reddens `the_jump_step_observes_the_coin_counter_before_it_drives` at tests/evidence_battery.rs:6222:5; (2) capping the probe loop at one attempt reddens `a_level_that_spawns_the_player_above_its_floor_still_shows_a_grounded_jump_arc` at :6303:5; (3) neutering seal_violations' hash check reddens `the_dr82_seal_reddens_on_a_block_edit_and_a_prose_edit` at tests/append_only_guard.rs:566:9.  None of the three is unfalsifiable",
        "I reproduced SIX of the six plants the report publishes, each on C:\\dr85acc_scratch, each red at the report's published line, each restored byte-exactly (restored sha256 equals the pristine sha256 for every one): p1 -> 6222:5, p2 -> 6303:5, p3 -> 4803:5, p4 -> append_only_guard.rs:313:5, p5 -> 313:5, p6 -> 4487:5.  My p2/p4/p5 mutated hashes are byte-identical to the batch's own published mutated hashes",
        "no test was removed and the ignored set is unchanged: my census of tests/*.rs between 5e840aa^ and 5e840aa finds 451 -> 454 test functions (+3, the three names above) and ZERO removed names across all 58 test files (no file added, none removed); src/adapter/godot.rs has 24 `#[test]` attributes before and after and its `mod tests` starts at line 6322, far below every DR-85 hunk",
        "the ignored set is exactly the seven e0..e6 names, before and after (my --list --ignored: 7 lines, exit 0)",
        "my forced-rebuild gate: 61 `target/debug/.fingerprint/hof-rs-*` directories removed with Python glob + shutil.rmtree (0 left), all 97 tracked `*.rs` paths touched individually from `git ls-files '*.rs'` (97 total), then `cargo test --offline` -> `Compiling hof-rs v0.1.0 (F:\\moonbit-hof-rs)` on log line 1, `Finished test profile ... in 1m 10s`, 60 result blocks, 602 passed / 0 failed / 7 ignored, 0 FAILED and 0 panicked lines, EXIT 0; `cargo test --offline -- --list` exit 0 with 609 `: test` lines; `cargo test --offline -- --list --ignored` exit 0 with 7",
        "the listing arithmetic is fully consistent: the lib unit block is 155 passed, the integration listing is 454, 155 + 454 = 609 listed, 609 - 7 ignored = 602 passed; the report's baseline 606 / 599 is 609 - 3 and 606 - 7, so it is arithmetically consistent with my own run plus the census (I did not re-run the baseline build)",
        "the report's gate numbers match mine item for item: 602/0/7, listing 609, 60 blocks, exit 0, 0 FAILED/panicked, and `cargo fmt --all --check` exits 0 (my own run: FMT_EXIT=0 on the delivered tree)",
        "one non-material discrepancy: the report removed 122 fingerprint directories and I removed 61.  The 122 is explained by their script's two build phases (the baseline phase built with the HEAD blobs swapped in, leaving 61 stale fingerprint directories behind, then the final phase's removal counted both sets); the load-bearing facts - 0 left and a forced Compiling line - I reproduced"
      ]
    },
    {
      "id": "A6-UNCHANGED",
      "title": "the arc rule, the ground probe's fail-closed behaviour, the ordering, every criterion, the frozen PRD, and the machine block",
      "pass": true,
      "evidence": [
        "arc rule byte-identical: `shows_an_arc` extracts identically from 5e840aa^ and 5e840aa (`self.rise > 0.0 && !self.monotone_fall`, sha of the extracted text f5df5998626fe744 both sides), as do `player_is_resting_on_ground` (d24090583e82d049), `verdict` (54e0e1be9a32e508) and `coin_count` (bea173849c268f94); my plant making shows_an_arc unconditionally true reddens a_jump_window_with_no_rise_is_rejected_too at tests/evidence_battery.rs:4487:5, exactly the batch's published p6 line",
        "ground probe fail-closed byte-identical: my plant making player_is_resting_on_ground accept every non-empty series reddens a_level_with_no_usable_ground_reports_the_jump_unobserved at :4803:5, exactly the batch's published p3 line; the waiting loop did not make the predicate permissive",
        "the ordering is unchanged: run() still drives step_input_jump before step_interaction_evidence, step_input_channel_probe and step_input_replay (src/adapter/godot.rs:686-689), and DR-85's only edit to that line is the new scene_tree argument; GROUND_NEEDING_BATTERY_STEP, GROUND_CONSUMING_BATTERY_STEPS, COIN_OBSERVING_BATTERY_STEP and COIN_CONSUMING_BATTERY_STEPS have identical values before and after, as do JUMP_GROUND_EPSILON (0.001), JUMP_GROUND_PROBE_FRAMES (2), JUMP_NOT_DRIVEN and COIN_COUNTER_PREFIX",
        "no criterion moved: .spec/hof-rs/REQUIREMENTS.md is 298a9489... and .spec/hof-rs/PRD-mario.md is 4c81c3a9... - the same values the report publishes and the same values the DR-83/DR-84 acceptances recorded; the commit touches four paths only (the three changed files plus its own report) and contains no grading code",
        "no game was written: the DR-85 commit's numstat is 4 files (the report, godot.rs, evidence_battery.rs, append_only_guard.rs); an mtime walk under runs/** finds 0 files newer than my boundary 1790967912 (2026-10-03 03:05:12, ~15 min BEFORE the commit) among 7,117 files, and 0 newer among 743 files under .workspace/**; newest under each is the same pre-existing file the report names",
        "the machine block parses and round-trips: exactly one ```json fence, 15 top-level keys, json.dumps(block, ensure_ascii=False, indent=2) reproduces the fence byte-for-byte (13,608 B, sha256 21366a3fc1603645642533acd0883443134e33f5ac2e15c9ed90310ed3a6f3e4); the out-of-repo file the report names as the block's first landing point (C:\\Users\\wyl\\AppData\\Local\\Temp\\dr85\\machine_block_dr85.json) does not exist now, so I could not compare file versus fence - DR85A-5 (info)",
        "residual-list adjudication: every 'measured' item I could reach reproduced (the six plants and their lines and byte-exact restores; the frozen arithmetic; the gate; the frozen hashes; pure LF; nothing pushed; zero writes under runs/** and .workspace/**), and the one I did not re-run (the 599/0/7 baseline) is arithmetically implied; every 'inferred' item is correctly labelled and none is load-bearing except the 2-frames-per-probe assumption, which I flag as the main risk; a real round CAN still find the jump undriven in the three declared shapes, and a coin CAN still be counted before it is observed in the one declared shape"
      ]
    },
    {
      "id": "A7-GUARDS",
      "title": "forbidden zones, frozen files, engine tree, dependencies, line endings, and push state",
      "pass": true,
      "evidence": [
        "runs/** and .workspace/**: 0 files newer than the boundary, 7,117 and 743 files walked, newest files pre-existing - my own os.walk, twice (before and after the gate)",
        "frozen hashes unchanged at the end of the acceptance: PRD-mario.md 4c81c3a9..., REQUIREMENTS.md 298a9489..., DECISIONS.md 245befb7..., Cargo.toml e0c4992b..., Cargo.lock d98fa915..., TASK-DR82-REPORT.md ee881850...; no dependency was added",
        "engine: godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe 194,216,960 B sha256 08483088...e9e6a, nested repo HEAD fc63af77c33368c4a1bb839c95d19750554f63a3 with an empty `git status --porcelain`",
        "line endings: godot.rs, evidence_battery.rs, append_only_guard.rs and the DR85 report are all CR = 0 / CRLF = 0 (pure LF), matching the byte census; no line-ending rewrite",
        "nothing pushed: HEAD = 5e840aade50efad38dd806c3a9e5249b655f0f79, origin/master = f6ea2d1c9e82da0add93f512d25a28f06306ae3b, `git diff --cached --name-only` empty, working tree clean apart from the four pre-existing untracked root scratch files (l.json, p2.json, pv.json, r.json)",
        "my writes were confined to C:\\Users\\wyl\\AppData\\Local\\Temp\\dr85acc (helpers, logs, JSON) and C:\\dr85acc_scratch (a copy outside the repository); the only repository write is this acceptance file - I wrote nothing under runs/**, no workspace directory, no report other than mine, no godot-mcp/**, and I edited DECISIONS.md nowhere.  No rm -rf, no path built from an unexpanded variable, no git checkout --, no git restore",
        "the gate's forced rebuild touched the mtime of all 97 tracked .rs files (required by the brief) and rewrote target/; no content changed - the working-tree sha256 of every reviewed file still equals both the published value and the committed blob"
      ]
    }
  ],
  "plants": [
    {
      "id": "q1",
      "where": "F:\\dr85acc_scratch\\src\\adapter\\godot.rs",
      "plant": "jump coin baseline can never match the counter prefix (starts_with(COIN_COUNTER_PREFIX) -> a token that never matches), i.e. the pre-jump reading is not taken",
      "target": "the_jump_step_observes_the_coin_counter_before_it_drives",
      "result": "RED exit 101 tests\\evidence_battery.rs:6222:5",
      "restore": "sha256 back to 8ff8b643..., equal"
    },
    {
      "id": "q2",
      "where": "scratch src/adapter/godot.rs",
      "plant": "cap the probe loop at one attempt (`while settle_attempts < 1`), the pre-DR-85 one-shot probe",
      "target": "a_level_that_spawns_the_player_above_its_floor_still_shows_a_grounded_jump_arc",
      "result": "RED exit 101 tests\\evidence_battery.rs:6303:5; mutated sha 01e2d5f6... identical to the batch's p2",
      "restore": "byte-exact"
    },
    {
      "id": "q3",
      "where": "scratch src/adapter/godot.rs",
      "plant": "player_is_resting_on_ground accepts every non-empty series (fail open)",
      "target": "a_level_with_no_usable_ground_reports_the_jump_unobserved",
      "result": "RED exit 101 tests\\evidence_battery.rs:4803:5",
      "restore": "byte-exact"
    },
    {
      "id": "q6",
      "where": "scratch src/adapter/godot.rs",
      "plant": "shows_an_arc unconditionally true",
      "target": "a_jump_window_with_no_rise_is_rejected_too",
      "result": "RED exit 101 tests\\evidence_battery.rs:4487:5",
      "restore": "byte-exact"
    },
    {
      "id": "q4",
      "where": "F:\\dr85acc_scratch\\.spec\\hof-rs\\tasks\\TASK-DR82-REPORT.md",
      "plant": "in-place machine-block edit 16 -> 17 inside the frozen prefix",
      "target": "the_dr82_census_claim_carries_its_dr84_qualifier",
      "result": "RED exit 101 tests\\append_only_guard.rs:313:5; mutated sha 4bb2ce2d... identical to the batch's p4",
      "restore": "byte-exact ee881850..."
    },
    {
      "id": "q5",
      "where": "scratch TASK-DR82-REPORT.md",
      "plant": "in-place prefix prose edit 逐名普查 -> 逐名统计",
      "target": "same",
      "result": "RED exit 101 tests\\append_only_guard.rs:313:5; mutated sha 7846e017... identical to the batch's p5",
      "restore": "byte-exact"
    },
    {
      "id": "q7 (mine)",
      "where": "scratch tests/append_only_guard.rs",
      "plant": "neuter the seal's hash comparison (`if actual != pin_sha` -> `if false && ...`)",
      "target": "the_dr82_seal_reddens_on_a_block_edit_and_a_prose_edit",
      "result": "RED exit 101 tests\\append_only_guard.rs:566:9, while the main DR-82 pin went GREEN - the non-vacuity pin catches a neutered seal",
      "restore": "byte-exact"
    }
  ],
  "counterexamples_i_constructed": [
    "apex-coin level, real battery: raw/input_jump.json call order baseline(0,3) < ground_probe(7) < play_input_recording press(10), with `Coins: 0` in the first baseline call and a JUMP_ARC_OBSERVED reading - the ordering property holds in the artifact, not only in the test",
    "counterexample level with the probe never supported: exactly 16 probes, no game-process press, no jump_reading, ok = false - the cap is bounded and fail-closed",
    "unreadable probe: exactly 1 probe, PROBE_UNREADABLE, no reading, ok = false - an unreadable channel is not waited on",
    "spawn-drop level: exactly 4 probes, press on the landing probe, not on the cap",
    "HUD with no readable counter: the jump step records COIN_BASELINE_UNREADABLE and the interaction window records COIN_COUNTER_UNREADABLE (the residual-1 branch works, though no repository test pins it)",
    "counter unreadable at the baseline but readable later (baseline match disabled): the transition is lost, the interaction window emits COIN_NOT_PICKED_UP although the jump collected the coin, and only COIN_BASELINE_UNREADABLE discloses it - the residual is real",
    "black-box re-implementation of whole_line_offset/seal_violations in Python over the real bytes, independent of the Rust helper: the seal marker is found at 44184, the heading at 44185, bytes[..44184] hashes to the pin, and the marker occurs once"
  ],
  "defects": [
    {
      "id": "DR85A-1",
      "severity": "minor",
      "what": "The unreadable-baseline branch of the coin observation has no test in the repository.  `grep` over tests/** for JUMP_COIN_BASELINE_UNREADABLE / COIN_BASELINE_UNREADABLE returns nothing; only the readable path (the apex-coin level) is pinned.  The residual the report leans on is exactly this branch, so a future edit that made the baseline silent (a `Some(\"Coins: 0\")` default, or dropping the summary) would leave every test green while the report's 'nothing is silent in that case' claim stop being true.",
      "reproduction": "grep -rn 'COIN_BASELINE_UNREADABLE' tests/ -> no match; my scratch test acc_unreadable_coin_baseline_is_recorded_not_silent (InteractionMode::UnreadableCounter) passes and shows the branch works today: jump observation carries COIN_BASELINE_UNREADABLE and no `Coins: 0`, interaction carries COIN_COUNTER_UNREADABLE, and the baseline attempt is still a labelled call.  Adding that test (or an equivalent) to tests/evidence_battery.rs would close the gap."
    },
    {
      "id": "DR85A-2",
      "severity": "info",
      "what": "The machine block says the pre-jump reading 'sits immediately ahead of the injection'.  In the raw artifact it is ahead of the injection but not adjacent: for the apex-coin level the order is baseline calls at indices 0-3, editor_side_injection at 4, the two stale-action clears at 5-6, the ground probe at 7, the before-frame at 8, create_input_recording at 9, and the press at 10.  The property that matters (before the press) holds; the adverb overstates the proximity.",
      "reproduction": "my inspection of raw_input_jump_apex.json (baseline_index 0, probe_index 7, press_index 10)."
    },
    {
      "id": "DR85A-3",
      "severity": "info",
      "what": "The report's forced-rebuild count of 122 removed fingerprint directories is not reproducible by the obvious method: `target/debug/.fingerprint/hof-rs-*` is 61 directories, and target/release has only 5.  The likely cause is that the implementer's gate runs two build phases (the baseline phase builds with the HEAD blobs swapped in and leaves 61 stale fingerprint directories, then the final phase's removal counts both sets).  The number is not load-bearing: 0 remained and the rebuild was forced in both runs.",
      "reproduction": "python glob of target/debug/.fingerprint/hof-rs-* -> 61 before and 61 after my own rebuild; my gate removed 61 and left 0; read_gate.py:158-161 shows the same single pattern the batch used."
    },
    {
      "id": "DR85A-4",
      "severity": "info",
      "what": "The report's residual description understates the residual's consequence.  It says the case is 'a HUD whose counter becomes readable only later in the run' and that 'no transition is claimed'; in fact the interaction window then reads the same value twice and emits COIN_NOT_PICKED_UP (its own `text:neq` assertion is refused), i.e. a verdict that the coin was not picked up, while the jump collected it.  The disclosure exists (COIN_BASELINE_UNREADABLE in the jump step) but the later window's contradicting verdict is not mentioned.",
      "reproduction": "scratch mutant disabling the baseline match + apex-coin level: my acc_residual_unreadable_baseline_loses_the_transition passes only in the mutant shape, asserting jump observation COIN_BASELINE_UNREADABLE, interaction observation `Coins: 1` twice and COIN_NOT_PICKED_UP; the code path is src/adapter/godot.rs:3381-3388."
    },
    {
      "id": "DR85A-5",
      "severity": "info",
      "what": "The report names C:\\Users\\wyl\\AppData\\Local\\Temp\\dr85\\machine_block_dr85.json as the block's first landing point and as compared back before the report was written, but that file does not exist now (the rest of the dr85 helper directory does, including verify_block.py).  I could verify the fence round-trips through json.dumps but not the file-versus-fence comparison the report's prose implies.",
      "reproduction": "ls C:\\Users\\wyl\\AppData\\Local\\Temp\\dr85\\machine_block_dr85.json -> No such file or directory; verify_block.py in the same directory only round-trips the fence."
    },
    {
      "id": "DR85A-6",
      "severity": "info",
      "what": "Stale head in the machine block (the DR84A-5 class, harmless here): head/origin_master are f6ea2d1c and the three changed files are described as uncommitted working-tree modifications, while the tree now sits on the local commit 5e840aa (dispatcher's commit, 03:20:52, four minutes after the report's mtime) with origin/master still f6ea2d1.  The description was true when written, nothing was pushed, and every published hash equals the committed blob, so the reviewed revision is unambiguous.",
      "reproduction": "git rev-parse HEAD -> 5e840aa; git rev-parse origin/master -> f6ea2d1; stat -c %y TASK-DR85-REPORT.md -> 2026-10-03 03:16:33; git show -s --format=%ct 5e840aa -> 1790968852 = 03:20:52."
    }
  ],
  "risks": [
    "Engine-side and therefore unverified: that each repeated running_game_get_node_property_samples call advances the game by the requested two physics frames.  The whole settle wait is worth 32 frames only under that assumption; if an engine re-read the same frame, a level that spawns in the air would read flat y and the window would be certified mid-air - a false positive, the opposite failure direction from the one the fix targets.  The report does label this as inferred; a real round must confirm a falling y on the first attempt and a flat y on a later one.",
    "Engine-side and unverified: that a coin inside the jump's apex is collected on the press in the body-entered shape the fixture models, that the extra node-property reads before the probe do not disturb real physics, and that a resting y really means supported.",
    "A level that collects a coin before the baseline read (a coin overlapping the spawn, or a collection driven by the level's own _ready) would still have its 0 -> 1 transition destroyed, and the harness cannot see it: the baseline would already read 1.  Not named by the report.",
    "A drop longer than ~32 frames (~0.53 s) is refused honestly (JUMP_NOT_DRIVEN), so E3 remains unmet on such a level; the report states this.",
    "The two-frame flat-y ground proxy is unchanged and remains a level-shaped risk (an apex on a moving platform, a level-specific player script); the batch narrows but does not close it.",
    "The interaction window can emit COIN_NOT_PICKED_UP while the jump collected the coin whenever the baseline read cannot see the counter (DR85A-4); a Tester reading only the interaction step would draw the wrong conclusion, the disclosure living in a different step's observation.",
    "The unreadable-baseline branch is unpinned by any test (DR85A-1).",
    "tests/round_artifacts_sidecar.rs rewrites one tracked sidecar under .spec on every cargo test, byte-identically; my required gate run performed that rewrite (git status shows no diff for it).",
    "The suite is slow (my forced-rebuild run: the evidence_battery binary alone reports 433.19 s, another 142.84 s and a 95.96 s one), so the gate must stay a background job."
  ],
  "unverified": [
    "Everything engine-side: no engine was started and no round was run, so the settle wait, the coin baseline against a real HUD, the repeated probe's frame advance, and the node-property reads' effect on physics are all untested here.",
    "The report's pre-change baseline (599 passed / 0 failed / 7 ignored, listing 606, 60 blocks, exit 0): I did not re-run it.  It is arithmetically consistent with my own run (609 listed - 3 new = 606; 606 - 7 ignored = 599) and with the census (no test removed), and the batch's own baseline_run.log / gate_summary.json record it, but I did not reproduce the swap-in of the HEAD blobs.",
    "The batch's own plant executions for p1/p3/p6 byte for byte: I reproduced the same six properties with my own mutations at the same published lines, and my p2/p4/p5 mutations are byte-identical to theirs, but I did not rerun their exact p1/p3/p6 byte edits.",
    "The out-of-repo machine block file named by the report (absent; DR85A-5).",
    "Which tests dominate the 433-second evidence_battery binary; I observed the binary's own reported time but did not profile it.",
    "The lib's internal 155 unit tests beyond their passing status: I counted 24 `#[test]` attributes in src/adapter/godot.rs before and after and confirmed every DR-85 hunk lies below line 4600 while `mod tests` starts at 6322, but I did not read them."
  ],
  "what_i_did_not_check": [
    "Did not start, stop or inspect any engine process; ran no round; made no network call; used no real HUD.",
    "Did not write anything under runs/**; did not modify any workspace directory, any existing report, the frozen specification, DECISIONS.md or godot-mcp/**.  The only repository write is this acceptance file plus the pre-existing byte-identical sidecar rewrite the test suite performs (git status shows no diff for it).",
    "Used no rm -rf (fingerprints were removed with Python glob + shutil.rmtree), built no path from an unexpanded shell variable, and never used git checkout --/git restore.",
    "Did not stage, commit or push anything.",
    "All tampering was confined to F:\\dr85acc_scratch (a copy outside the repository) and to helper scripts and outputs under C:\\Users\\wyl\\AppData\\Local\\Temp\\dr85acc; every scratch source was restored byte-exactly with sha256 after each plant, and the real TASK-DR82-REPORT.md was never written.",
    "Worked alone; delegated nothing.",
    "Did not line-by-line audit all 293 changed lines of src/adapter/godot.rs or all 278 of tests/evidence_battery.rs; I audited the diff, the changed call paths, the constants, the fixtures the new tests use, and everything I could exercise.",
    "The gate's forced rebuild touched the mtime of the 97 tracked .rs files (the brief requires it); their contents are unchanged."
  ],
  "advice_for_the_next_batch": [
    "Pin the unreadable-baseline branch: add a test on a HUD with no readable counter asserting the jump step carries COIN_BASELINE_UNREADABLE and no `Coins: 0`, and the interaction window carries COIN_COUNTER_UNREADABLE (DR85A-1).  It costs one battery run.",
    "On hardware, confirm the settle wait's premise: the first jump:ground_probe on the frozen smoke-t15 level should read a MOVING y (the 23.9 px spawn drop) and a later attempt a flat y.  If the first probe already reads flat, the level is grounded at the scene's first frames and the cap is never used; if every probe of a falling player reads flat, the probe call does not advance game time and the wait is a false-positive hazard - that would be a stop-the-line finding.",
    "Report the residual's consequence, not only its condition: when the counter is unreadable at the baseline, the interaction window's COIN_NOT_PICKED_UP is not evidence the coin was not collected (DR85A-4).",
    "Do not call the reading 'immediately ahead of the injection' (DR85A-2); say 'ahead of the press in the same raw document'.",
    "Keep the fingerprint count out of the claims as an exact number (DR85A-3): 'fingerprints cleared, 0 left, rebuild forced with the Compiling line on log line 1' is the reproducible form.",
    "State plainly that the reviewed revision is now the local commit 5e840aa (unpushed) when the report's machine block predates the commit (DR85A-6), and make the out-of-repo block file durable or stop naming it (DR85A-5)."
  ]
}
```

## 0. What this file is

Independent acceptance of the **TASK-DR85** offline batch, written by a fresh subagent with no
upstream conversation context.  The reviewed report
[`TASK-DR85-REPORT.md`](TASK-DR85-REPORT.md) was read as a lead, never as evidence.  Everything
below was produced here: the code reading, the raw-artifact inspection, seven plants, six
purpose-built counterexample probes, the test census and the forced-rebuild gate.  The
machine-readable block above was produced with
`json.dumps(..., ensure_ascii=False, indent=2)`, written first to
`C:\Users\wyl\AppData\Local\Temp\dr85acc\verdict_block_dr85a.json` (outside the repository),
parsed back with `json.loads` and re-serialised to the identical bytes before this file was
written.

**Verdict: `pass`.**  Both majors the DR-84 acceptance opened are closed.  (1) The jump step
observes the coin counter before it drives and the reading is the first call of
`raw/input_jump.json`, strictly ahead of the press; the residual road (a counter not readable at
the baseline) is real, disclosed and reproduced.  (2) The DR-82 pin now pins the reviewed
44,184-byte revision through `seal_violations`, and both plants the previous acceptance used now
redden it at `tests/append_only_guard.rs:313:5`.  The spawn drop is waited for inside a bounded
32-frame cap against a measured 11.1-frame drop, with both fail-closed directions intact.  I
reproduced all six of the batch's plants at their published lines (three with byte-identical
mutated hashes), reproduced the forced-rebuild gate at **602 passed / 0 failed / 7 ignored,
listing 609, exit 0**, and every guard holds.  Six findings are recorded, all `info` or `minor`;
none invalidates the deliverable.

## 1. Item-by-item table

| # | item | what I verified myself | result |
|---|---|---|---|
| 1 | **coin order (headline)** | `step_input_jump` reads the counter first (`godot.rs:2219-2233`, `:2261-2302`) and hands the calls in as `leading_calls` (`:2328`); the raw `input_jump.json` of the apex-coin level has baseline at call 0-3, probe at 7, press at 10, with `Coins: 0` in the first baseline call | **pass** |
| 2 | **same candidate set** | both readers use `scene_tree` from the same `step_play_scene()` snapshot (`:686-687`), `hud_label_candidates`, the same `properties:["text"]` call, the same string coercion and the same `Coins:` prefix rule | **pass** |
| 3 | **the residual road** | unreadable baseline: the jump step records `COIN_BASELINE_UNREADABLE`, the interaction window records `COIN_COUNTER_UNREADABLE` (my ACC-6); later-readable counter: the `0 -> 1` transition is destroyed and the interaction window emits `COIN_NOT_PICKED_UP` although the jump collected the coin (my mutant ACC-4) - the report names the case, not the consequence (DR85A-4) | **pass, gap named** |
| 4 | **why not the consumer list** | the coin test requires `observing < input_jump`; the ground test requires `input_jump < observing` - literally contradictory, and the structural pin keeps both lists inside the three horizontal steps | **pass** |
| 5 | **prefix seal** | `bytes[..44184]` sha256 = `319397fd...e406` == `git show 930229b^:` of the report; marker `\n# 附：DR-84...` at 44184, heading at 44185, one occurrence; both plants RED at `:313:5` (mutated hashes byte-identical to the batch's p4/p5); the neutering plant reddens the non-vacuity pin at `:566:9` | **pass** |
| 6 | **spawn drop** | bounded 16 x 2 frames; the measured drop is 23.925201416016023 px / 0.18487525298356502 s / 11.092515 frames; 16 probes at the cap with no press and no reading; 1 probe for an unreadable channel; 4 probes on the settling level with the landing probe as the certified one | **pass** |
| 7 | **tests** | all new tests run the real `Orchestrator` + `godot_adapter` with only `tools` replaced; 451 -> 454 test functions, zero removed, ignored 7 -> 7 (the e0..e6 names); all three new tests shown falsifiable by my own plants | **pass** |
| 8 | **gate** | forced rebuild (61 fingerprints cleared, 97 literal `.rs` paths touched one by one) -> `Compiling` on log line 1, 60 blocks, **602/0/7**, 0 FAILED/panicked, exit 0; `--list` 609, `--list --ignored` 7; the 599 baseline is arithmetically implied (609-3, 606-7) | **pass** |
| 9 | **unchanged** | `shows_an_arc`, `player_is_resting_on_ground`, `verdict`, `coin_count`, five ordering/geometry constants and the run() order are byte-identical to `5e840aa^`; REQUIREMENTS/PRD/DECISIONS/Cargo hashes unchanged; commit touches 4 files, no game | **pass** |
| 10 | **guards** | 0 files newer than my boundary under `runs/**` (7,117 walked) and `.workspace/**` (743); engine clean and identical; pure LF; nothing staged/committed/pushed by me; HEAD `5e840aa` local, origin still `f6ea2d1` | **pass** |
| 11 | **machine block** | one fence, 15 keys, round-trips byte-for-byte (13,608 B); the out-of-repo file it names is gone (DR85A-5); its head is stale relative to the dispatcher's later commit (DR85A-6) | **pass, info** |

## 2. My own plants and counterexamples

All tampering happened in `F:\dr85acc_scratch` (a copy outside the repository, byte-refreshed from
the delivered tree) or in helper scripts and outputs under
`C:\Users\wyl\AppData\Local\Temp\dr85acc`.  The repository itself was never written except for
this file.  Every planted file was restored from a byte backup and hash-verified.

| # | plant (on the copy) | intended test | observed |
|---|---|---|---|
| q1 | the coin baseline can never match the prefix (the pre-jump reading is not taken) | `the_jump_step_observes_the_coin_counter_before_it_drives` | **RED** exit 101 `tests\evidence_battery.rs:6222:5` |
| q2 | cap the probe loop at one attempt | `a_level_that_spawns_the_player_above_its_floor_still_shows_a_grounded_jump_arc` | **RED** `:6303:5`; mutated sha identical to the batch's p2 |
| q3 | `player_is_resting_on_ground` accepts every non-empty series | `a_level_with_no_usable_ground_reports_the_jump_unobserved` | **RED** `:4803:5` |
| q6 | `shows_an_arc` unconditionally true | `a_jump_window_with_no_rise_is_rejected_too` | **RED** `:4487:5` |
| q4 | DR-82 machine-block value `16 -> 17` | `the_dr82_census_claim_carries_its_dr84_qualifier` | **RED** `tests\append_only_guard.rs:313:5`; mutated sha identical to p4 |
| q5 | DR-82 prefix prose `逐名普查 -> 逐名统计` | same | **RED** `:313:5`; mutated sha identical to p5 |
| q7 (mine) | neuter the seal's hash comparison | `the_dr82_seal_reddens_on_a_block_edit_and_a_prose_edit` | **RED** `:566:9`, while the main DR-82 pin turned GREEN |

Six purpose-built probes (scratch-only, never in the repository): `acc_unreadable_probe_is_refused_at_once`
(1 probe, `PROBE_UNREADABLE`, no reading, `ok=false`), `acc_probe_cap_is_bounded_and_fail_closed`
(exactly 16 probes, `JUMP_NOT_DRIVEN` after "16 probe attempt(s)", no reading, `ok=false`),
`acc_settling_drives_on_the_landing_probe_not_the_cap` (4 probes, `JUMP_ARC_OBSERVED`),
`acc_unreadable_coin_baseline_is_recorded_not_silent` (`COIN_BASELINE_UNREADABLE`, no `Coins: 0`,
`COIN_COUNTER_UNREADABLE`), `acc_residual_unreadable_baseline_loses_the_transition` (passes only
in the mutant shape, demonstrating the residual), and `acc_dump_raw_documents` (which produced the
three `raw_input_jump_*.json` I inspected).  I also re-implemented `whole_line_offset` /
`seal_violations` in Python over the real report bytes, independently of the Rust helper.

## 3. Independent judgement, by job

**3.1 The coin decision.**  The code does exactly what the report says: the reading is taken
before the pass drives and becomes the pass's leading calls, so it is the first thing in
`raw/input_jump.json`.  The candidate sets are identical by construction because both readers use
the same tree snapshot and the same rule.  The property that matters is preserved in the readable
case and honestly labelled in the unreadable case.  The road is the right one: adding the jump to
`COIN_CONSUMING_BATTERY_STEPS` is not merely inelegant but contradictory with the ground rule, and
declaring the hazard without reading would leave the transition destroyed.  What I would correct
is the phrasing: nothing prevents the counter from changing before the observing window; what the
batch guarantees is a *recorded pre-jump value*.  And a coin can still be counted before it is
observed when the counter is unreadable at the baseline and readable later - the report names the
case, I reproduced it, and the interaction window then makes a `COIN_NOT_PICKED_UP` claim the
jump's own collection contradicts.

**3.2 The prefix seal.**  This is now a real seal, not a heading check.  It pins the very revision
the DR-84 acceptance reviewed, taken from git rather than from prose; it is not shifted by a byte;
both plants redden it where they used to stay green; and the non-vacuity pin is itself falsifiable.

**3.3 The spawn drop.**  The wait is bounded, justified against a drop I recomputed myself, and
drives on the level's landing probe rather than on the cap.  Both fail-closed directions survive:
an unreadable probe is refused immediately, and a player still moving at the cap is refused with
no reading and `ok=false`.  The residual "a longer drop" is stated honestly.  The load-bearing
unknown is that a repeated probe really advances two physics frames; that is labelled inferred and
is the first thing a round batch should watch.

**3.4 The tests and the gate.**  The tests go through the real adapter and read the raw documents
it wrote; the census shows three added and none removed; the ignored set is unchanged; and the
three new tests are declared pins rather than preserved first reds, which the report states
plainly.  Each of the three is falsifiable, shown by my own plants.  The gate reproduces at
602/0/7, listing 609, exit 0, under a forced rebuild.  The only gap is that the unreadable-baseline
branch - the residual's own branch - has no test.

**3.5 What was not changed.**  Every rule the previous acceptance pinned is byte-identical, the
order is unchanged, the frozen product requirements and the ledger are untouched, no game was
written, and the machine block parses and round-trips.  One publication nit: the reviewed revision
is now the local commit `5e840aa`, which the report's block predates.

**3.6 Guards.**  Nothing under `runs/**` or any workspace directory, no frozen file, no engine
path, no dependency, no line-ending rewrite, nothing pushed.  My only repository write is this
file and the suite's own byte-identical sidecar rewrite.

## 4. Unverified items, with reasons

See the `unverified` array.  The load-bearing ones: everything engine-side (no engine ran, so the
settle wait's frame-advance premise, the coin collection shape and the physics-neutrality of the
extra reads are untested); the report's pre-change 599 baseline, which I did not re-run but whose
arithmetic follows from my own run and the census; the batch's exact p1/p3/p6 mutated bytes (I
reproduced the properties, and p2/p4/p5 byte-for-byte); and the out-of-repo block file, which no
longer exists.

## 5. What I did not check

No engine, no round, no network; nothing under `runs/**` and no workspace directory touched; no
existing report, frozen specification, `DECISIONS.md` or `godot-mcp/**` modified; no `rm -rf`, no
path built from an unexpanded variable, no `git checkout --`/`git restore`; nothing staged,
committed or pushed.  I did not line-by-line audit all 293 changed lines of `src/adapter/godot.rs`
or all 278 of `tests/evidence_battery.rs`, and I did not read the lib's 155 unit tests beyond
confirming their count, their passing status and that the diff lies outside their module.  The
forced-rebuild gate touched the mtime of the 97 tracked `.rs` files as the brief requires; their
contents are unchanged.

## 6. Advice for the next batch

See `advice_for_the_next_batch`.  In one line: pin the unreadable-baseline branch, and on hardware
confirm that the first jump ground probe on the frozen level reads a *falling* `y` - if the probe
call does not advance the game's physics, the settle wait certifies a player it should refuse.
