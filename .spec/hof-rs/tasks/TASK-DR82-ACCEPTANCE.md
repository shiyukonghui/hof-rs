```json
{
  "verdict": "pass",
  "task": "TASK-DR82-ACCEPTANCE",
  "kind": "independent acceptance of the DR-82 offline batch; no engine, no round, no network; nothing staged, committed or pushed; nothing written under runs/**",
  "reviewed_report": ".spec/hof-rs/tasks/TASK-DR82-REPORT.md",
  "reviewed_report_sha256": "319397fdb369ea95c63e2eac7d4eaacd25b7825e73313e9afe863f5eb1a8e406",
  "reviewed_report_bytes": 44184,
  "reviewed_task_book": ".spec/hof-rs/tasks/TASK-DR82.md",
  "reviewed_task_book_sha256": "0a5e07e74bd0475010935ef0c273c8ad39a4160141e031afed3fd3599316e4ff",
  "head_at_acceptance": "7bac271539a55ba1df02187bdef465341805df12",
  "origin_master_at_acceptance": "199ce37a370fa8f968d64c1bc9d4a6db2ee8340f",
  "pushed": false,
  "verdict_scope": "Every one of the four items is implemented and independently reproduced. The headline jump rule is real: a jump window is injected in the game process only after a two-frame position probe says the player rests on the ground, an unreadable or insufficient probe fails closed, and a window that is not driven carries no jump_reading and is named JUMP_NOT_DRIVEN, while a driven window whose series does not rise above its own first sample can never be scored JUMP_ARC_OBSERVED. The regression fixture is the previous round's own series verbatim: I extracted the 30 samples of the frozen raw/input_replay.json call 31 and they are exactly, float for float, the 30 numbers in the test; the rule rejects that series (rise 0.0, monotone, JUMP_DEGENERATE_FALL) and accepts a genuine arc. The redaction item is real and is stronger than the report claims: linking the built library and running the production entry on byte-copies of the frozen trajectories redacts both spellings (planner 76353 -> 74665 with 40 spans, developer 994873 -> 994137 with 38, tester 1080415 -> 1080013 with 27, all still valid JSON, idempotent, only the four empty credential keys left), and an accidentally stale 16:00 library that knew only the escaped spelling produced exactly the disclosed false green (zero spans on the real unescaped shape). The append-only corrections are genuine appends: the 41045-byte prefix of TASK-DR81-REPORT.md hashes to 7834f2d7...8efc8, which is both the value TASK-DR81-ACCEPTANCE.md reviewed and the committed blob at c4a30fa, and a mirrored seal caught a one-byte edit, a deleted line and a same-length rewrite on temporary copies while accepting a pure append. The leftovers hold: a root-level ACCEPTANCE.md is accepted by the hook and a ledger verify returns exit 0 with OK: 48 record(s), the second correction sits entirely after the seal, the two window branches have tests, and the masking direction is an executable test. I reproduced the gate myself: cargo test --offline exit 0 with 589 passed / 0 failed / 7 ignored, --list 596, fmt exit 0, exactly 14 added tests and 0 removed, the seven ignored names unchanged; all six plants reddened their own target with exit 101 at the very line the report publishes and all three files were restored byte-exactly (sha256 identical to HEAD). Guards hold: runs/** and .workspace/** unchanged, PRD/DECISIONS/REQUIREMENTS/Cargo/engine tree byte-identical, nothing pushed. Defects are report-accuracy and scope items only; no load-bearing claim is false.",
  "criteria": [
    {
      "id": "C1-JUMP-RULE",
      "title": "the headline: a jump window is driven only from the ground and a degenerate window is never an observed jump",
      "pass": true,
      "evidence": [
        "src/adapter/godot.rs:2289-2345: for action == 'jump' the harness takes a two-frame running_game_get_node_property_samples probe labelled jump:ground_probe immediately before the injection; resting is player_is_resting_on_ground(required_sample_pairs(parsed)); the read failure path returns false",
        "src/adapter/godot.rs:2371-2385: airborne_before_jump forces game_injected = false, so semantic_inject_action is never called for that window; jump_driven is set only by a real game-process injection",
        "src/adapter/godot.rs:2475-2485: entry['jump_reading'] is attached only when action == 'jump' && jump_driven, so a refused window has no scoreable reading",
        "src/adapter/godot.rs:2508-2528: arc_failure = Some(reading) whenever shows_an_arc() is false; that sets ok = false and the observation names the verdict (JUMP_DEGENERATE_FALL / JUMP_NO_RISE) and never JUMP_ARC_OBSERVED",
        "src/adapter/godot.rs:3946-3957: player_is_resting_on_ground returns false for None, for fewer than two samples, and for any y that moves by more than JUMP_GROUND_EPSILON = 1e-3 - all three are fail-closed",
        "src/adapter/godot.rs:3985-3987: shows_an_arc() = rise > 0.0 && !monotone_fall, computed by jump_reading_of over min and monotonicity, not by comparing endpoints",
        "regression fixture: I parsed runs/smoke-t15/iter-1/candidate/.hoh/deterministic/raw/input_replay.json, took the 30-sample window at call 31 (x unique 1, x 3690.02734375, y 1492.81433105469 -> 2552.92553710938) and compared it to the vec! in tests/evidence_battery.rs:4212-4243: 30 numbers, all exactly equal (float and text). rise = 0.0, monotone_fall = True, shows_an_arc = False, verdict JUMP_DEGENERATE_FALL",
        "the same extraction shows every one of the four windows in that file (calls 7, 19, 31, 43) has min at index 0 and rise 0.0, so the whole round contains no upward motion",
        "the genuine arc the test accepts is computed independently: (0..30) 283.0 - max(5f - 0.2f^2, 0) -> rise 31.2, monotone_fall False, shows_an_arc True, JUMP_ARC_OBSERVED",
        "the seven jump tests are in the suite and all report ok in my own cargo test run"
      ],
      "judgement": "Principled, not tuned. The predicate is a definition ('the highest point must come after the window's first sample'), with an exact 0.0 boundary and no fitted epsilon, and it cannot reject an upward arc recorded from the ground: such a series starts at the ground and its minimum is strictly below its first sample, so rise > 0. What it can reject is a window whose first sample already sits at or after the apex (rise = 0) - a conservative false negative, not a false pass, and in the normal drive order unreachable because the probe immediately precedes the injection. The one substantive observation is that the second conjunct is redundant: rise > 0 already implies not-monotone-fall, because a series whose minimum is strictly below its first sample cannot be non-decreasing."
    },
    {
      "id": "C2-REDACTION-SHAPE",
      "title": "the headline: the JSON-key shape, in the frozen files, by my own two methods",
      "pass": true,
      "evidence": [
        "my census (python, two independent methods plus the naive third): for every one of the seven frozen runs/smoke-t15/iter-1/traj/*.json, the JSON-aware key walk finds exactly 16 target names as keys and the raw-byte escaped spelling (\\\"NAME\\\") finds 0 - the report's disagreement, reproduced exactly",
        "the naive guarded scan (?<![A-Za-z0-9_])NAME= reproduces the report's trap byte for byte: planner.attempt1.json 1 reported vs 28 real, developer.attempt1.json 0 vs 26 (fully false green), tester.attempt1.json 15 vs 15",
        "per-name census of the key shape: 12 HOH_* names (10 previously declared + HOH_TOOLS_POLICY + HOH_WORKSPACE) plus the 4 credential names, each exactly once in every file; DSH_TERM_CMD, HOH_SECRET_PATH, PATH and Path are absent from that shape - the report's table is exact",
        "the four credential keys carry the empty string in every file, as published",
        "runs/smoke-t14 carries the same 16 keys in every trajectory file, so the vector is pre-existing, as published",
        "decisive: I linked the built library and ran the production function redact_named_assignments_and_keys_traced on byte-copies of all seven frozen files (copies proven byte-identical to the sealed originals). planner 76353 -> 74665 (40 spans), developer.attempt1 994873 -> 994137 (38), developer.attempt2 235198 -> 234946 (12), tester 1080415 -> 1080013 (27); every output is still valid JSON, and a second pass leaves only the four empty credential keys with 0 raw values. The three fragment/nesting probes (top-level object, an env-nested object, and the exact bytes of the planner env object) all redact their key values",
        "causal corroboration of the disclosed false green: my first link accidentally used the stale target/debug/libhof_rs.rlib built at 16:00, and that build produced spans = 0 and left every key value raw - precisely the false green the report discloses. After cargo build refreshed the rlib from the current source the same probe redacts",
        "sealed originals still carry the raw form: every original has keys_raw = 12, keys_redacted = 0",
        "the two new tests go through the real entry point (redact_tree_traced) and are green in my run"
      ],
      "judgement": "Both spellings are handled, the frozen encoding is the one that matters, and it is the encoding the implementation now scans. No name family escapes: the rule set is the 4 credentials, the 14 HARNESS_ENV_VARS entries (including DSH_TERM_CMD, PATH/Path and HOH_SECRET_PATH) and the 2 newly declared names, and a token census of every HOH_*/DSH_* identifier in both frozen rounds found no name outside that set except HOH_BIN, which occurs only as 'HOH_BIN=$HOH_HOH_BIN' - a shell variable reference whose value is another covered name, not a value. Residual shapes that would still escape: the JSON-key scan requires a string value with no newline between the key and the colon, so a dump writing a bare number, null or a line-broken key would not be redacted; and the frozen sidecars are not re-redacted, so the vector survives in the existing evidence (see defect DR82A-1 and the risk list)."
    },
    {
      "id": "C3-APPEND-ONLY",
      "title": "the correction to the previous report is an append under a sealed prefix",
      "pass": true,
      "evidence": [
        "TASK-DR81-REPORT.md is 47548 bytes; the byte offset of the whole-line heading '# 附：DR-82 ③ 更正' is exactly 41045, so the pin's byte count is real",
        "sha256 of those first 41045 bytes = 7834f2d71d970d5a27b95c6fcc5a339525616c3a08bfe23dbf20e9ac8048efc8, which is exactly TASK-DR81-ACCEPTANCE.md's object.report_sha256_at_review (and its report_bytes 41045)",
        "the same 41045 bytes are the committed blob: git show c4a30fa:.spec/hof-rs/tasks/TASK-DR81-REPORT.md has 41045 bytes and that sha256; cb507e8 still holds the earlier 35203-byte revision the previous acceptance described as superseded - so the prefix is the reviewed revision, not a reconstruction",
        "because the prefix is byte-identical, the original text and the original machine-readable json block inside it are untouched; the second correction (A-3) begins at a later offset, so both corrections live in the appended region",
        "mirrored seal arithmetic (the test's own whole_line_offset + prefix sha256) on temporary copies outside the repository: one byte flipped inside the prefix -> prefix-sha violation; the first line deleted -> offset 40747 != 41045; a same-length rewrite at byte 5000 -> prefix-sha violation; a pure append after the heading -> no violation. The repository file was never touched",
        "the pin test the_dr81_report_prefix_before_the_dr82_correction_is_frozen is green in my run and additionally asserts the correction heading, 'smoke-t15', 'filesystem_cache10', the A-3 heading and 'OK: 48 record(s)'"
      ],
      "judgement": "A genuine append with the strongest possible seal: the pinned prefix is not merely internally consistent, it is the revision the previous acceptance reviewed. The pin test would catch an in-place edit - I demonstrated the arithmetic three ways on copies - though the demonstration is a faithful mirror of the test rather than the test itself, because running the Rust guard on a mutated repository copy would have required modifying the report."
    },
    {
      "id": "C4-LEFTOVERS",
      "title": "A-2, A-3, A-4 and risk (a)",
      "pass": true,
      "evidence": [
        "A-2: .githooks/hoh-acceptance-lib.sh now matches '*.md' (was '*/*.md'); I sourced the library and exercised hoh_is_acceptance_report directly: ACCEPTANCE.md, TASK-DR82-ACCEPTANCE.md and sub/ACCEPTANCE.md are accepted; /abs/ACCEPTANCE.md, ..\\ACCEPTANCE.md, '.', NOTES.md, TASK-SMOKE-T15-REPORT.md and ACCEPTANCE.txt are refused - so the implementation matches the rule's wording and its refusal message, and the refusals are unchanged",
        "A-2's test a_repo_root_level_acceptance_artifact_is_accepted_as_the_marking_source is green, and restoring '*/*.md' reddens it (my plant p4, exit 101 at tests/push_gate.rs:101:5)",
        "A-3: the second correction '# 附：DR-82 ④（A-3）更正' begins after the 41045-byte seal, so it is append-only and the machine block is inside the frozen prefix",
        "A-3's reading is independently confirmed read-only: sh scripts/accept-commit.sh verify -> exit 0, 'accept-commit: OK: 48 record(s)', ledger mtime and size unchanged by the call; .git/hoh-accepted-commits.txt has 48 'accepted ' records and line 45 names .spec/hof-rs/tasks/TASK-SMOKE-T14-ACCEPTANCE.md, exactly as the correction states",
        "A-4 count growth: partition_editor_errors_in_window is a multiset comparison (position + swap_remove), and the test drives anchor [E] with judged [E,E] then [E,E,E]; the test is green and my plant p6 - dropping the swap_remove, i.e. a set comparison - reddens it (exit 101 at tests/common/mod.rs:312:13)",
        "A-4 anchor absent: an absent anchor returns every judged line as new; the test makes the wide editor_get_errors call fail outright in the channel, is green, and my plant p5 - the fail-open return - reddens it (exit 101 at tests/common/mod.rs:312:13)",
        "risk (a): the_window_can_still_open_on_a_project_that_is_broken_on_disk writes scripts/project.gd with class_name Ground to the workspace, has the reload never re-emit the error line, and asserts the file really is on disk, launchable == true, anchor_line_count 1, project_defects_new 0 and pre_existing_lines 0; it is green"
      ],
      "judgement": "All four leftovers are closed at the standard the task asked for: A-2 by making the implementation match its own documentation (and the widening is disclosed in the hook comment), A-3 by an append that is inside the same seal, A-4 by two tests that each have a plant proving they are load-bearing, and risk (a) by an executable statement of the limit rather than prose."
    },
    {
      "id": "C5-GATES-PLANTS",
      "title": "the gate reproduced, and the six plants re-run",
      "pass": true,
      "evidence": [
        "my own cargo test --offline: exit 0, 589 passed / 0 failed / 7 ignored across 60 result blocks; the report's 589/0/7 and exit 0 are reproduced exactly",
        "cargo test --offline -- --list: 596 'NAME: test' lines, i.e. 582 + 14, matching the report",
        "cargo fmt --all --check: exit 0",
        "delta by parsing the DR-82 commit's diff for #[test]/#[tokio::test]: 14 added, 0 removed; the 14 names are exactly the 7 jump tests, the 2 secret_hygiene tests, the 3 launchable_gate tests, the 1 push_gate test and the 1 append_only_guard test, and all 14 report ok",
        "ignored: exactly the seven e0..e6 names, each 'ignored', unchanged",
        "all six plants re-run by me (byte backup, mutate, run the exact target test, restore from the backup, compare bytes and sha256): p1 exit 101 panicked at tests/evidence_battery.rs:4044:5; p2 exit 101 at tests/evidence_battery.rs:4197:5; p3 exit 101 at tests/secret_hygiene.rs:740:5; p4 exit 101 at tests/push_gate.rs:101:5; p5 exit 101 at tests/common/mod.rs:312:13; p6 exit 101 at tests/common/mod.rs:312:13. Every line is the line the report publishes",
        "restoration: sha256 before == after for all three files (godot.rs cca12db4a49d5f4d582a839d4f0534754890f44de99a6d00fe9fcb3f8c5ae57e, secrets.rs 8796f204b6291c2a08b005bb9927dd6a159204d6b2fe97c562f482f60ec4277a, hoh-acceptance-lib.sh ac260ec354650e4c269c63eff4b9befd3d501610fb40d38b427969b17ac045a0 - all three equal to the values the report publishes and to HEAD's content), byte comparison equal, and git diff --exit-code is clean afterwards",
        "the p5/p6 disclosure is accurate and verbatim: both redden as 'FakeHarness step #2 expects Developer but the runtime asked for Tester; actual sequence so far: [\"planner\", \"developer\", \"tester\"]' at tests/common/mod.rs:312-316, i.e. a harness role-sequence panic rather than the test's own assertion. It is still a valid red for the target test (the flipped verdict suppresses the DR-24 repair retry the scripted step would consume), and the report says exactly that",
        "no plant output shows a compile error: every red is a runtime panic in the target test, and every plant exited 101 with the target test FAILED and 'finished in' seconds"
      ],
      "judgement": "The gate reading, the delta arithmetic, the ignored set and the six plants all reproduce. The one thing I cannot reproduce is the report's ordering claim (which tests genuinely reddened before their implementation): the seven jump tests and the three window tests are plant-red by the report's own admission, and my re-run confirms plant-red only."
    },
    {
      "id": "C6-GUARDS",
      "title": "forbidden zones, frozen artifacts, and the machine-readable block",
      "pass": true,
      "evidence": [
        "runs/**: the newest file is runs/smoke-t15/evidence/COPY_MANIFEST.txt at 2026-10-02 14:54:52, earlier than the batch boundary (TASK-DR82.md, 15:02:13); zero files are newer, both before and after my own runs",
        ".workspace/**: the newest file is .workspace/fresh-t15/.godot/.gdignore at 15:14:59 (1 byte), next 14:30:51; unchanged by my runs. The batch's own writes are much later (.spec mtimes 18:06-19:10), so 15:14:59 predates it, but who wrote it is not attributable from here (T15A-7 already recorded it)",
        "PRD .spec/hof-rs/PRD-mario.md = 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a, byte-identical to the frozen value",
        "DECISIONS.md = 245befb7af292c379c161ddc917e996a54a4dceea5e93c5d0226816efbae4a76, unchanged; D289, D293 and D294 read and consistent with the batch's reading of the append-only discipline",
        ".spec/hof-rs/REQUIREMENTS.md = 298a948929a434a91b9088f4d566b7e387d0cfeb270f86a79d88b006821e0e54; Cargo.toml = e0c4992b...; Cargo.lock = d98fa915... - all unchanged, so no dependency was added",
        "engine: godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe 194216960 bytes sha256 08483088a4a2772841cd3b4c916b2d45b3cb6255656cf3951598a86fce7e9e6a; nested repo HEAD fc63af77c33368c4a1bb839c95d19750554f63a3 with an empty git status --porcelain",
        "line endings: all eleven files the DR-82 commit touches under src/, tests/, .githooks/ and .spec/ are CR = 0 / CRLF = 0 (pure LF)",
        "push: HEAD is 7bac271539a55ba1df02187bdef465341805df12 (one local commit ahead of origin/master) and origin/master is still 199ce37a370fa8f968d64c1bc9d4a6db2ee8340f, the value at the batch's start; the origin/master reflog's newest 'update by push' entry is 199ce37a, so nothing was pushed",
        "the batch commit 7bac271 touches exactly 11 files (the 9 code/test/hook files, TASK-DR81-REPORT.md and TASK-DR82-REPORT.md) - no PRD, no DECISIONS.md, no Cargo file, no godot-mcp/**",
        "no new temporary object is tracked or untracked in the repository: git status --porcelain shows only the four pre-existing root scratch files l.json/p2.json/pv.json/r.json (untracked before this batch)",
        "machine block: the report contains exactly one json fence; it parses to 12 top-level keys and json.dumps(..., indent=2) of the parsed object equals the fence body byte for byte; it carries the required task/kind/head/baseline/gate/items/plants/forbidden_zones/unverified fields and its gate block repeats 589/0/7/596/exit 0"
      ],
      "judgement": "Every guard the task names holds under my own instruments. Two nuances are recorded rather than hidden: (i) the test suite itself rewrites one tracked sidecar under .spec byte-identically on every cargo test, so 'no repository file touched' is a content claim, not an mtime claim; (ii) the machine block's head is the pre-commit value, while the repository now carries the dispatcher's local commit of exactly those files."
    }
  ],
  "defects": [
    {
      "id": "DR82A-1",
      "severity": "minor",
      "what": "The item-2 census counts key presence, which the fix preserves, and the report never states that the frozen *.redacted.json sidecars are still raw behind those keys. Every T15 sidecar carries its 12 non-empty HOH_* key values in plain text (keys_raw = 12, keys_redacted = 0), and the assignment form of the two newly declared names also survives in the frozen sidecars (HOH_TOOLS_POLICY= and HOH_WORKSPACE=, twice each in planner and developer, 8 occurrences). The report's unverified item 4 says the production redactor was not applied to the frozen files, which covers this, but a reader of the headline 'JSON-key redaction' can reasonably conclude the existing evidence is clean. No credential value is involved.",
      "reproduction": "read runs/smoke-t15/iter-1/traj/*.redacted.json and count (\"NAME\"\\s*:\\s*\"(?!<redacted>)) plus NAME= occurrences: 12 raw key values and 8 raw assignment occurrences per the two files; my census scripts do it in two independent ways"
    },
    {
      "id": "DR82A-2",
      "severity": "info",
      "what": "The `!monotone_fall` conjunct of shows_an_arc is logically redundant - rise > 0 already implies the series is not non-decreasing - and no test makes it the decisive rejection: a_monotone_fall_is_not_recorded_as_an_observed_jump uses a fixture whose ground probe already refuses the window, so the rejection comes from the probe, not from the arc rule. The report's tables are individually accurate (its RiseZero row says only the rise half can reject it), but the machine block's item description 'y not monotone' and the test name suggest the second half carries weight of its own.",
      "reproduction": "src/adapter/godot.rs:3985-3987; tests/evidence_battery.rs:4058-4084 (JumpMode::AirborneNoGround makes ground_probe_positions report a moving y) versus tests/evidence_battery.rs:492-505"
    },
    {
      "id": "DR82A-3",
      "severity": "info",
      "what": "A jump window the harness refused to drive still emits 'jump: POSITION_ASSERT_PASSED' in the step observation, because the positional assertion runs whenever a quadruple exists. The step is correctly ok = false and the observation carries JUMP_NOT_DRIVEN and no jump_reading, so no criterion is falsely met; but a reader who greps POSITION_ASSERT_PASSED still sees a 'passed' assertion for an undriven jump - the same delivered != observed confusion the batch removes at the verdict level. No test asserts its absence.",
      "reproduction": "src/adapter/godot.rs:2584-2592 (assert_replay_moved runs after the probe refusal, which only skips the injection at 2371-2385)"
    },
    {
      "id": "DR82A-4",
      "severity": "info",
      "what": "A tracked file outside the declared change list has a mid-batch mtime: .spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/analysis/redaction_defect.redacted.txt at 19:05:17, byte-identical to HEAD. The cause is pre-existing behaviour, not a DR82 change: tests/round_artifacts_sidecar.rs::build_sidecar() writes that sidecar back into the repository on every cargo test, which my own run did at 19:36:33. The report's section 8, which enumerates what the repository gained, does not mention it.",
      "reproduction": "tests/round_artifacts_sidecar.rs:106-131 (std::fs::write(&sidecar_path, ...)); stat the file before and after any cargo test"
    },
    {
      "id": "DR82A-5",
      "severity": "info",
      "what": "The report's machine block and its 'HEAD = start = end = 199ce37a, 未提交' line are statements about the moment the report was written; the repository a reader now sees has one local commit on top, 7bac271, containing exactly the eleven DR82 files. Nothing is pushed, so the claim that this batch did not push is true; only the head reading is stale.",
      "reproduction": "git rev-parse HEAD vs the machine block's head; git show --stat 7bac271"
    }
  ],
  "risks": [
    "The jump rule is fixture-proved only: no engine ran, so the two-frame ground probe, the epsilon and the rise boundary have never been exercised against real physics. The report says this and it is the batch's main limitation.",
    "The fix converts the T15 false pass into an honest 'unobserved', not into an observed jump. On a level whose ground ends before the jump window the jump class will now be reported JUMP_NOT_DRIVEN and E3 will still not be met; making E3 met on hardware needs the drive order or the window to be bounded so the jump is pressed while is_on_floor() holds - the batch records that as a deliberate non-goal.",
    "The ground probe is a proxy for geometry. Two frames of flat y can also be read at a jump apex or on a moving platform (false positive), and a resting player whose y jitters by more than 1e-3 would be refused (false negative). A window whose first sample lands at or after the apex is rejected rather than scored.",
    "The disclosure vector is closed in the code but not in the existing evidence: the frozen trajectories and their sidecars still carry paths, role, run id and a loopback URL.",
    "The JSON-key scan requires a string value with no newline between the key and the colon; a differently serialized dump (a bare number, null, or a line-broken key) would escape the key rule even though the assignment rule would still catch NAME=.",
    "Risk (a) - the pre-reload window can open on a project that is still broken on disk - is now an executable fact, so it is knowingly accepted. If a disk-side probe is added, that test must be reddened deliberately rather than adjusted.",
    ".workspace/fresh-t15/.godot/.gdignore was written at 15:14:59, before this batch's own writes but after the T15 round; its author is unknown (T15A-7 recorded the same). A later acceptance must not treat fresh-t15 as frozen.",
    "target/debug/libhof_rs.rlib can lag target/debug/deps/libhof_rs-*.rlib: my first independent link picked up a stale 16:00 library and produced a false green. Future acceptors must cargo build (or link the deps rlib) before drawing conclusions from the built library.",
    "Everything about the gate window's real-hardware behaviour remains artifact-level: DR-81 (1)'s infrastructure branch was again not exercised on hardware this round, and the window's log-tail reading is known to be unstable."
  ],
  "unverified": [
    "No engine, no round, no network: every hardware-side statement in this acceptance is a reading of frozen artifacts, and the new probe/arc rule has never run against a live game process.",
    "The report's ordering claims about first reds cannot be reproduced after the fact. I reproduced the plants (all six red at the published lines) but not the claim that two secret_hygiene tests genuinely reddened before their implementation; the report itself classifies the jump and window tests as plant-red only.",
    "The implementer's baseline story (two pre-existing hygiene tests red because the test binaries were stale, green after a forced rebuild) and its derived counts (61 fingerprints removed, 1376 s suite time) cannot be checked post hoc. I reproduced the endpoint 575/0/7 -> 589/0/7 only as the final 589/0/7 (I did not rebuild the pre-DR82 revision).",
    "Whether the implementer started an engine: I can only show that runs/** has no file newer than 14:54:52, that .workspace/** has no file newer than 15:14:59 and that the engine binary and nested repository are byte-identical; I did not monitor processes.",
    "A-2's widening on a real ledger and a real push: I exercised the predicate directly and the sandbox test, but the task forbids staging or pushing, so no real push was attempted.",
    "The silent-drift hazard of DR82A-4 aside, I did not line-by-line audit the batch's 2720 inserted lines, the analysis scripts, or the PNG evidence."
  ],
  "what_i_did_not_check": [
    "Did not start, stop or inspect any engine process, run any round, or use the network.",
    "Did not write anything under runs/**; all temporary scripts, backups, copies and outputs live in C:\\Users\\wyl\\AppData\\Local\\Temp\\dr82acc.",
    "Did not modify the reviewed report, TASK-DR81-REPORT.md, the frozen specification, DECISIONS.md, godot-mcp/**, or any workspace directory; did not stage, commit or push anything; used no rm -rf, built no path from an unexpanded variable and never used git checkout to restore a file.",
    "Did temporarily mutate three source files to re-run the six plants; all three were restored from byte backups and verified with sha256 and byte comparison, and git diff --exit-code is clean.",
    "Did not re-run the suite after the plants (the green 589/0/7 run was taken before them, on the pristine tree); the restoration proof is byte identity with the tree that produced that run.",
    "Did not reimplement the Rust redactor; the decisive redaction evidence is the real built function called through its public entry point on frozen copies."
  ]
}
```

## 0. 机器可读判定（由 `json.dumps(..., ensure_ascii=False, indent=2)` 生成并**先落盘**到仓外 `verdict_block.json`，回读 `json.loads` 后再写入本文件；写入后再次从本文件抠出栅栏并解析、与落盘字节比较）

- **总判定：`pass`**。四项全部落实并被独立复现；六处植入全部按报告公布的行号红；门读数、增量、`ignored`、守卫全部复现。缺陷均为**报告准确性/范围**类，没有一条承重陈述为假。
- 本验收全程**离线**：未起引擎、未跑轮次、未联网；**未在 `runs/**` 写一个字节**；未 stage/commit/push；临时物全在仓外。

---

# TASK-DR82-ACCEPTANCE — 独立验收：跳跃地面探针与弧判据、JSON 键形脱敏、追加式更正与四处遗留

- 验收者：**全新独立验收子代理**（无上游对话上下文；不继承实施者与调度者结论）
- 被验收对象：`.spec/hof-rs/tasks/TASK-DR82-REPORT.md`（sha256 `319397fd…a8e406`，44,184 B，纯 LF）——**只用于定位，不作证据**
- 任务书：`.spec/hof-rs/tasks/TASK-DR82.md`（sha256 `0a5e07e7…16e4ff`，7,203 B）
- 复核基线：`TASK-SMOKE-T15-REPORT.md` / `TASK-SMOKE-T15-ACCEPTANCE.md`、`TASK-DR81-REPORT.md` / `TASK-DR81-ACCEPTANCE.md`、`DECISIONS.md` **D289/D293/D294**、`REQUIREMENTS.md`
- 验收时点：2026-10-02 19:2x–19:5x (+0800)；`HEAD = 7bac271`（DR-82 的 11 个文件，**本批之前由派遣方提交**）、`origin/master = 199ce37a`（**未推送**）

---

## 1. 逐项核对表

| # | 检查项 | 我的独立读数 | 判定 |
|---|---|---|---|
| **C1** | 跳窗只在有地面处被驱动；退化窗口永不被记为已观测跳跃；探针不可读时 fail-closed | `godot.rs:2289-2345` 探针（2 帧，标签 `jump:ground_probe`），`2371-2385` 空中则不注入、`jump_driven` 只由真实注入置位，`2475-2485` 只对已驱动窗口写 `jump_reading`，`2508-2528` `shows_an_arc=false ⇒ ok=false` 且绝不命名 `JUMP_ARC_OBSERVED`；`3946-3957` `None`/不足 2 帧/y 变动 > 1e-3 **全部** fail-closed | **通过** |
| **C1b** | 回归夹具**就是**上一轮自己的序列 | 从冻结 `raw/input_replay.json` call 31 取出的 **30 个 y** 与 `tests/evidence_battery.rs:4212-4243` 的 `vec!` **逐浮点相等**；`rise=0.0`、`min@0`、单调 ⇒ 拒绝；真实弧 ⇒ `rise=31.2`、非单调 ⇒ 接受 | **通过** |
| **C1c** | 弧阈是否只是对那一条序列调参？会不会拒真弧？ | 判据是定义式（首样本不得是窗口最小值），边界精确 `0.0`、无拟合 epsilon；真弧从地面起跳必然 `rise>0` ⇒ 不会拒。可拒的是"首样本已在顶点/之后"（`rise=0`）的保守假阴；且 `!monotone_fall` 与 `rise>0` **逻辑冗余**（见 DR82A-2） | **通过（附观察）** |
| **C2** | 两种计数法交叉 + 冻结文件里的 16 个键 | 我的方法：JSON 感知键遍历 = **16/文件**，转义拼写原始字节 = **0** ⇒ **两法不一致，与报告逐字一致**；naive 守卫生扫描 = planner **1** / developer **0** / tester **15**（真实 28/26/15）⇒ **假绿陷阱复现** | **通过** |
| **C2b** | 两种拼写现在都被处理（**决定性**） | 用 **真实构建的库** 调生产入口 `redact_named_assignments_and_keys_traced` 跑**冻结文件的逐字节副本**：planner 76353→**74665**（40 span）、developer.attempt1 994873→**994137**（38）、developer.attempt2→**234946**（12）、tester→**1080013**（27）；输出全部仍是合法 JSON、二次通过只剩 4 个空凭据键（raw=0） | **通过** |
| **C2c** | 是否还有族或拼写逃逸 | 规则集 = 4 凭据 + 14 `HARNESS_ENV_VARS`（含 `DSH_TERM_CMD`/`PATH`/`Path`/`HOH_SECRET_PATH`）+ 2 新名；对两轮冻结件做 `HOH_*/DSH_*` 令牌普查，**唯一**规则外名字是 `HOH_BIN`，只出现在 `HOH_BIN=$HOH_HOH_BIN`（值是另一个已覆盖名，不是值） | **通过（附残余形状）** |
| **C3** | 追加式更正 + 封印前缀哈希 = 上一轮验收复核值 | 标题 `# 附：DR-82 ③ 更正` 的 whole-line 偏移 **恰好 41045**；前 41045 B 的 sha256 = `7834f2d7…8efc8` = `TASK-DR81-ACCEPTANCE.md` 的 `report_sha256_at_review` = **`c4a30fa` 的已提交 blob**（`cb507e8` 里仍是更早的 35203 B 版本）⇒ 原文与机器可读块逐字节未动 | **通过** |
| **C3b** | pin 会不会抓住就地编辑（**临时副本植入**） | 镜像封印算术在**仓外副本**上：前缀内翻 1 字节 ⇒ 前缀 sha 违规；删首行 ⇒ 偏移 40747≠41045；同位改写 ⇒ sha 违规；**纯追加 ⇒ 无违规** | **通过** |
| **C4** | A-2 / A-3 / A-4 两条分支 / 风险(a) | A-2：`*.md`（原 `*/*.md`），我**直接 source 该库**逐路径演练（根级 `ACCEPTANCE.md` 接受；`/abs`、`..\`、`.`、`NOTES.md`、`*-REPORT.md`、`.txt` 全拒）。A-3：第二节更正在 41045 之后；`sh scripts/accept-commit.sh verify` ⇒ **exit 0 / OK: 48 record(s)**（台账 mtime、size 未变），第 45 行来源 = `…TASK-SMOKE-T14-ACCEPTANCE.md`。A-4：`partition_editor_errors_in_window` 是**多重集**比较（`position` + `swap_remove`），两条测试都在。风险(a)：测试断言磁盘上确实损坏、`launchable=true`、`anchor_line_count=1`、`project_defects_new=0`、`pre_existing_lines=0` | **通过** |
| **C5** | 门 + 六处植入 | `cargo test --offline` **exit 0 / 589 passed / 0 failed / 7 ignored**；`--list` **596**；`fmt --all --check` **exit 0**；`#[test]` 差分 **+14 / -0**；`ignored` 七名未变。六处植入**全部 exit 101 且落在报告公布的行**；三文件逐字节回退（sha256 与 HEAD 一致、`git diff --exit-code` 干净） | **通过** |
| **C6** | 守卫与机器块 | `runs/**` 最新 `14:54:52` < 边界 `15:02:13`（我的运行后亦然）；`.workspace/**` 最新 `15:14:59`（早于本批自身写入窗口，作者不可归因）；PRD `4c81c3a9…`、DECISIONS `245befb7…`、REQUIREMENTS `298a9489…`、Cargo `e0c4992b…`/`d98fa915…`、引擎 `08483088…` 全未变；嵌套引擎仓干净；11 个改动文件 **CR=0**；`origin/master` 仍 `199ce37a`（未推送）；机器块唯一 `json` 栅栏、12 键、解析并逐字节往返 | **通过** |

---

## 2. 我自己做的植入与反例

### 2.1 三处"脱敏"反例（含一次**意外**的决定性复现）

1. **两种计数法互斥**：JSON 感知键遍历 16 vs 转义拼写原始字节 0 —— 冻结件用的是**真实对象键**（未转义），所以只认转义拼写的实现会把这些文件报成**干净**。
2. **naive 守卫生扫描的假绿**：`(?<![A-Za-z0-9_])NAME=` 在 `developer.attempt1.json` 上得 **0**（真实 26）——因为 JSON 串里 `
` 的字母 `n` 紧贴名字之前。planner 1（真实 28）、tester 15（真实 15）。**逐字复现报告的自曝**。
3. **意外但决定性**：我第一次链接外部检查器时，误用了 `target/debug/libhof_rs.rlib`（**16:00 的陈旧构建**，只认转义拼写），它在我**按测试夹具逐字构造**的顶层对象、嵌套 `env` 对象、以及**冻结 planner 文件的真实 env 字节片段**上，全部给出 **spans=0、键值原样存活** —— 正是报告 §2.2 披露的那个假绿。`cargo build` 刷新该 rlib 后，同一探针给出 **10/10/12 个 span** 并把键值全部换成 `<redacted>`。**缺陷与修复都被因果复现。**
   - 附带教训（记为风险）：`target/debug/libhof_rs.rlib` 可能落后于 `target/debug/deps/libhof_rs-*.rlib`；不接受"只在 target 里看"的证据。

### 2.2 封印植入（仓外副本）

| 植入 | 结果 |
|---|---|
| 前缀第 1000 字节翻 1 bit | 前缀 sha `3d490f9c…` ≠ pin ⇒ 违规 |
| 删掉首行 | 偏移 40747 ≠ 41045 ⇒ 违规 |
| 第 5000–5005 字节同长度改写 | 前缀 sha `a6041ed1…` ≠ pin ⇒ 违规 |
| 标题之后纯追加 | **无违规**（与"追加式"一致） |

### 2.3 六处植入（我重跑的，逐字节备份回退）

| # | 文件 | 我改的 | 目标测试 | 我的读数 |
|---|---|---|---|---|
| p1 | `src/adapter/godot.rs` | 地面谓词恒 true | `a_jump_window_over_a_gap_is_rejected_instead_of_passed` | exit 101，`tests\evidence_battery.rs:4044:5` |
| p2 | `src/adapter/godot.rs` | `shows_an_arc()` 恒 true | `a_jump_window_with_no_rise_is_rejected_too` | exit 101，`tests\evidence_battery.rs:4197:5` |
| p3 | `src/runtime/secrets.rs` | 关闭 `splice_json_keys` | `the_unescaped_role_config_dump_is_redacted_too` | exit 101，`tests\secret_hygiene.rs:740:5` |
| p4 | `.githooks/hoh-acceptance-lib.sh` | `*.md` → `*/*.md` | `a_repo_root_level_acceptance_artifact_is_accepted_as_the_marking_source` | exit 101，`tests\push_gate.rs:101:5` |
| p5 | `src/adapter/godot.rs` | 锚缺失改 fail-open | `an_absent_window_anchor_fails_closed` | exit 101，`tests\common\mod.rs:312:13` |
| p6 | `src/adapter/godot.rs` | 时间窗改集合比较（去掉 `swap_remove`） | `a_repair_that_reproduces_the_same_line_still_closes_the_gate` | exit 101，`tests\common\mod.rs:312:13` |

**回退证明**：`godot.rs` `cca12db4…ae57e`（297412 B）、`secrets.rs` `8796f204…4277a`（78976 B）、`hoh-acceptance-lib.sh` `ac260ec3…045a0`（7603 B）——三者在植入前、植入后、回退后**完全相同**，且 `git diff --exit-code` = 0。

**p5/p6 的红形态（我逐字复现了报告的口径）**：两条都表现为运行期 harness 角色序列 panic，**不是**测试自己的断言：
`FakeHarness step #2 expects Developer but the runtime asked for Tester; actual sequence so far: ["planner", "developer", "tester"]`（`tests/common/mod.rs:312`）。被翻转的判定使 DR-24 修复重试不再触发，脚本化的 Developer 步无人消费 ⇒ 这是**该分支被翻转的直接后果**，对目标测试有效，但读者必须知道它不是断言红。

---

## 3. 我的独立判断

1. **① 的方向正确，但承诺被如实收窄。** 真机威胁（T15 跳跃窗在地面结束之后被驱动）现在会在**探针**处被拒：既不注入、也不写 `jump_reading`，并写 `JUMP_NOT_DRIVEN`。"拒绝退化结果"因此有**两条彼此独立的防线**（探针拒绝 + 弧判据拒绝），且每条都有自己的红（p1/p2）。代价是：**在 T15 那种关卡上，跳跃类会变成"未观测"而不是"上抛弧线"**——这符合任务书允许的两条路之一，但它意味着下一轮若还是那个关卡布局，E3 仍不会 met。报告把它记为非目标，我认为这个取舍是可以接受的，但它必须被下一批当作**待清偿项**而不是已完成项。
2. **② 比报告自己证明得更强。** 报告诚实披露"未把生产脱敏器施加到冻结件"，只以等价夹具为证。我直接链接**真实构建的库**在生产入口上跑冻结件副本，两种拼写与 16 个键值全部被脱敏、输出仍是合法 JSON、二次通过幂等。这条证据链**独立于实现者的夹具**。
3. **③ 的封印质量最高**：pin 值不仅是"文件内部一致"，而**就是上一轮验收复核过的那一版**（也是 `c4a30fa` 的 blob）。
4. **④ 四条遗留全部按任务书标准关闭**：A-2 走"实现与文档一致"并**主动披露放宽了一个形状**；A-4 的两条分支各有植入证明其承重；风险(a) 被钉成**可执行事实**（将来加磁盘侧探针会让它**按设计变红**）。
5. **⑤ 门与植入全复现**，包括 p5/p6 那个"非断言红"的诚实披露——我逐字复现了它。
6. **⑥ 守卫成立**，但有两条nuance必须留在纸上：测试套件每次 `cargo test` 都会**逐字节重写**一个仓库内的 sidecar（`.spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/analysis/redaction_defect.redacted.txt`，我的运行也一样），所以"未触碰仓库"是**内容口径**；机器块的 `head` 是**提交前**读数，仓库现在多了一个仅本地的 `7bac271`。
7. **报告纪律**：报告对本批的自曝（首实现只认一种拼写、① 与 ④ 的首红是植入红、p5/p6 是非断言红、一次回退因文件锁失败后重试、基线曾因陈旧测试二进制先红）**全部经得起复核**，我未发现被掩盖的失败。

---

## 4. 缺陷（**只报不改**）

见机器块的 `defects`：**DR82A-1（minor）**、DR82A-2/3/4/5（info）。逐条复现方式已在块内给出。**没有一条使某个判据失真**，故总判定仍为 `pass`。

---

## 5. 未验证项（附原因）

见机器块 `unverified`。最要者三条：**无引擎**（一切真机侧结论都是工件读数）；**"真先红"的次序不可事后复现**（我只复现了植入红）；**本批是否起过引擎只能间接推断**（`runs/**` 无新文件、`.workspace/**` 无新文件、引擎树与嵌套仓逐字节未变）。

## 6. 我没有检查的

见机器块 `what_i_did_not_check`。要点：未起/未停任何引擎、未跑轮、未联网；未在 `runs/**` 写字节；未改被验收报告/`TASK-DR81-REPORT.md`/冻结规格/`DECISIONS.md`/`godot-mcp/**`/任何工作区；未 stage/commit/push；未用 `rm -rf`、未从未展开变量构造路径、未用 `git checkout --` 还原；临时物全在 `C:\Users\wyl\AppData\Local\Temp\dr82acc`。为复跑六处植入**临时改动过三个源文件**，均以字节备份回退并验证 sha256/逐字节。**未**在植入后重跑整套（绿色 589/0/7 取自植入前的干净树；回退是逐字节同一性证明）。

## 7. 给下一批的建议

1. **让 E3 在真机上真的 met**：要么把驱动窗口/顺序**有界化**（跳跃前确认在 `is_on_floor()`），要么在关卡要求里规定终点离地板右缘足够远；然后再跑一轮。现在的判据侧已经就位，但**它只会把假绿变成"未观测"**。
2. **把脱敏的计数改成"值与键都数"**：本批公布的普查只数键名出现次数，而修复**保留键、替换值**，所以那组数字无法区分"已处理"与"仍然原文"。下一批应公布 **raw value = 0** 的逐文件读数（我在机器块与 §2.1 里给了方法）。
3. **补一条真正驱动到弧判据的测试**：构造"探针读到静止（在地面）+ 窗口是单调下落"的夹具，让 `!monotone_fall`/`JUMP_DEGENERATE_FALL` 成为**决定性**判据；否则应考虑删掉冗余的合取项。
4. **被拒窗口不应再打印 `jump: POSITION_ASSERT_PASSED`**（或至少标注"undriven"），否则 grep 读者仍会误读成"跳成功"。
5. **重跑脱敏后生成新的旁路**（原文不动），或在报告里显式登记"冻结 sidecar 仍原文"为**已接受的遗留**——两种都行，但不能不说。
6. 任何"未触发/0 次/从未"的强断言，先在**其引用的载荷**里逐条扫一遍；任何"文件未被碰"的断言，先确认**测试套件自己**是否会回写它（本批的 T10 sidecar 就是一例）。
7. 将来做库级独立复现时，**先 `cargo build`** 再链接 `target/debug`（或直接链 `deps/`），否则会拿到陈旧 rlib 并得假绿。
