```json
{
  "task": "TASK-DR79-ACCEPTANCE",
  "kind": "independent acceptance of the additive erratum batch (no round executed, offline, runs/** read-only)",
  "reviewed": [
    "TASK-DR79.md",
    "TASK-DR79-REPORT.md (lead only)",
    "TASK-SMOKE-T13-REPORT.md (working copy + HEAD blob)",
    "TASK-SMOKE-T13-ACCEPTANCE.md",
    "TASK-SMOKE-T13-REPORT.md / DECISIONS.md D289 D293"
  ],
  "reviewed_at_head": "4c8e76a88f3ec0612d9b50300d6521dab8402fa7",
  "origin_master_at_review": "8ddbad3f4db43c28be158c17ad0678fe4d77857c",
  "verdict": "pass",
  "verdict_scope": "Every headline deliverable is independently reproduced: the erratum is 318 insertions / 0 deletions with the pre-existing 107,703 bytes byte-identical to HEAD and the machine-readable block byte-identical to machine_block.json; all three mechanism corrections recompute from the raw records (the initial start published :53068, the DR-70 warning belongs to the 04:41:38 repair restart, the 64 KiB path fired once, artifact_valid's looseness is :1378 workspace.is_dir()); the one refused correction (screenshot:2) is correctly refused; all four hygiene fixes have my own plants reddening the intended tests with byte-exact restore; the gate reproduces 59 suites / 554 passed / 0 failed / 7 ignored / exit 0 / 561 listed with REMOVED=0 and fmt clean; the guards hold. Two minor numeric defects live in the NEW appended material (two probe reply sizes; one stale sha in the corrected index row) and one repository-wide gap (no mechanical append-only guard). They contradict no mechanism claim, so the batch passes, but they should be fixed by a follow-up additive erratum before the next real round.",
  "criteria": [
    {
      "id": "ADDITIVITY",
      "pass": true,
      "evidence": "git diff --numstat -- .spec/hof-rs/tasks/TASK-SMOKE-T13-REPORT.md = 318 insertions / 0 deletions. HEAD blob = 107,703 B (sha256 f3f04fbb5c6b8086...); working file = 134,079 B; working[0:107703] == HEAD byte-for-byte (True); the appended 26,376 B begin with the literal bytes for a horizontal rule followed by '# 附：DR-79 勘误（**追加式**，2026-10-02）'. The append therefore carries every change; no original line can have been deleted or rewritten. A line-anchored fence scan finds exactly one ```json block (fences 741 and 1408, content 742..1407) whose text plus a single trailing LF is byte-identical to runs/smoke-t13/evidence/analysis/machine_block.json (34,699 B, sha256 36e34d0d04369206), so the machine-readable block and all evidence strings inside the original region are untouched by construction."
    },
    {
      "id": "ADDITIVITY-PLANT",
      "pass": true,
      "evidence": "Plants on temp copies (never on the repo file): (A) in-place edit of one original-region prose line -> prefix_identical_to_HEAD False, line diff shows 1 changed line; (B) deletion of one original-region line -> prefix False, 1 deletion; (C) in-place edit inside the json block -> prefix False AND the machine-block byte-identity check with machine_block.json False. So a reviewer's `git diff --numstat` / HEAD-prefix comparison / machine-block round-trip does catch tampering - but NOTHING in the repository does it automatically: no test, script or hook references TASK-SMOKE-T13-REPORT.md (grep over *.rs and *.py: 0 hits), and core.hooksPath=.githooks holds only the DR-75 pre-push acceptance-ledger gate. Registered as defect D-3."
    },
    {
      "id": "MECH-A-INITIAL-START-SUCCEEDED",
      "pass": true,
      "evidence": "evidence/round/game_endpoint_tools_list_round_author.json and ..._scene_tree_round_author.json both begin verbatim 'POST http://127.0.0.1:53068/mcp' and carry valid JSON replies (73 tools; scene tree /root/Main/Ground|Player|Goal|HUD). Their out-of-repo staging copies preserve the real capture mtimes: 2026-10-02 04:19:22.644865 and 04:19:22.841993 - so the '04:19:22' the DR-79 report could not recompute IS independently confirmed (to the second) by the staging bundle. developer.attempt2.json msg 77 (extra.timestamp 1790887442.749 -> 04:44:02.75) reads the game log and ends '[MCP] role=game configured_port=53068 source=cmdline listen=true / [MCP] listening on 127.0.0.1:53068 / [MCP] INFO: MCP server is ready on 127.0.0.1:53068'. The Godot user://logs directory (out of repo, read-only) decomposes the whole round: 04.41.23.log (687 B) carries exactly the configured_port=53068 session, 04.41.38.log and 04.54.38.log (199 B each) are banner-only = the two processes that never bound (pass 1's :55336 and the repair restart's :55361), and 04.54.50.log carries :51223 (battery pass 2). Hence the round's initial start published a live route, and the report's 'no route for any role until battery pass 2' is wrong."
    },
    {
      "id": "MECH-A-DR70-BELONGS-TO-THE-REPAIR-RESTART",
      "pass": true,
      "evidence": "warnings.log is 1,849 B / 7 newline-terminated lines (line 0 qa_scope = 212 B, line 1 DR-70 = 896 B, so 212+896+2 LF = 1,110 B). msg 135 (04:50:46) dir listing shows '04:41 1,110 warnings.log' -> the file's last write before the listing was 04:41, not 04:17:44. run_loop.rs appends MCP_SCOPE_WARNING at :778, BEFORE the first start_round_game at :832 -> the 04:41 write is the DR-70 line. HEAD has exactly three start_round_game call sites: :832 (round start), :1348 (inside the ':1343 if launch_gate.applicable && !launch_gate.launchable' repair block, i.e. the first thing that runs after battery pass 1 failed at 04:41:30/04:41:37), and :1427 (post-battery, and pass 2 succeeded on :51223 with 1 poll). The DR-70 line names http://127.0.0.1:55361/mcp; quarantine/deterministic-pass-1.stale-1790888078/raw/play_scene_ready.json names :55336 for pass 1. The failing start is therefore :1348. This upgrades the report's own 'strong inference' to a reconstruction supported by two independent artifact families (warnings.log size/mtime decomposition and the Godot log rotation timeline), though still without harness-level per-start instrumentation."
    },
    {
      "id": "MECH-A-TIME-AND-NARROWING",
      "pass": true,
      "evidence": "The refusal is at extra.timestamp 1790887888.1706953/...888.4060276/...888.4060276 (developer.attempt2 msgs 137/138/139, returncode 5 with the DR-43 text); epochs.txt anchors 1790885864 = 04:17:44 and 1790888078 = 04:54:38 give 1790887888 = 04:51:28.17, so the erratum's 04:31:28 -> 04:51:28 correction recomputes. The erratum's E-1 items 4/5/6 perform exactly the mandated narrowing: the 'flipped invariant' becomes 'the same round's two start_round_game calls had different fates', and the promise/behaviour risk is restricted to the repair window ~04:41 -> 04:54:51 (A1 created_at 1790888091 = 04:54:51); E-9 marks mechanisms.round_game_readiness_failure.{endpoint,consequence} and risks[3] superseded while leaving them verbatim."
    },
    {
      "id": "MECH-B-64KIB-FIRED-ONCE",
      "pass": true,
      "evidence": "Parsing (not grepping) extra over the four unredacted trajectories yields exactly one hit: tester.attempt1.json message 98, extra.hoh_output_truncated=true, hoh_output_limit_bytes=65536, hoh_output_original_bytes=81139, extra.timestamp=1790888197.46 = 04:56:37; the message text contains verbatim '[hoh: tool output truncated' and '[hoh: 65536 of 81139 bytes were carried; the remaining 15603 bytes were dropped and are NOT part of this result.]'. The other three trajectories have no such field. The report's '0 times / untriggered' and the machine block's truncation_64kib.triggered=false are therefore the opposite of the record, and the erratum registers the first real-machine exercise of that path."
    },
    {
      "id": "MECH-C-ARTIFACT-VALID-ATTRIBUTION",
      "pass": true,
      "evidence": "HEAD src/runtime/run_loop.rs: :1137 computes developer_artifact_valid once; :1147 uses it for attempt 1; :1154 gates the wrap-up block with 'if developer_limits && !developer_artifact_valid'; :1185 reuses the SAME value inside that block; :1378 sets 'artifact_valid: workspace.is_dir()' in the DR-70 launch-gate repair block. runs/smoke-t13/iter-1/result.json says wrap_up_retry_used=false, wrap_up_retry_reason='not_triggered', repair_retry_used=true, and developer attempt 2 artifact_valid=true while the broken scene should have made it false. So the report's 1137/1185 account points at a block that never ran, and the real looseness is the always-true directory check - exactly as the erratum now attributes it. The fix replaces :1378 with orchestrator.adapter.developer_artifact_valid(&workspace)."
    },
    {
      "id": "REFUSAL-SCREENSHOT-2",
      "pass": true,
      "evidence": "The acceptance's T13A-4 asserts a record-type table '{replay:11, runtime_trace:10, build:5, assert:3}' summing to 29 and omitting screenshot:2. It does not exist at any revision: HEAD line 296 and the earlier report commit 62ad5a0's line 296 both read verbatim 'MISSING=[]         record types {replay:11, runtime_trace:10, build:5, assert:3, screenshot:2}' (5 families, sum 31). My recomputation from iter-1/evidence.json gives {replay:11, assert:3, runtime_trace:10, screenshot:2, build:5} = 31, and evidence/analysis/round_facts.txt:161 lists the same five. The machine block's count_scopes has no record-type key at all. The acceptance's own `reproduction` field also prints screenshot:2, contradicting its `what`. Refusing to 'correct' this sub-item was right, and registering it as not-reproduced (erratum E-7) is the honest handling."
    },
    {
      "id": "FIX-USAGE-DOUBLE-COUNT",
      "pass": true,
      "evidence": "Code: usage_from_attempts' filter gains '&& !name.contains(\".redacted.\")'. My plant (removing exactly that line, LF anchor; restored byte-exact, sha256 0014353268346efb...9499) reddens tests/usage_extraction.rs::a_redacted_sidecar_is_not_a_second_attempt: exit 101, 'FAILED', panic at tests/usage_extraction.rs:121. Frozen non-vacuity: applying the OLD filter to runs/smoke-t13/iter-1/traj/ selects planner.attempt1.json + planner.attempt1.redacted.json; the NEW filter selects only planner.attempt1.json (developer 4 -> 2, tester 2 -> 1). planner.attempt1.json holds 27 usage calls / 272,378 tokens while iter-1/usage.json's planner summary says 54 / 544,756 = exactly 2x. The test pins ratio 1.0 with a sidecar and 2.0 once a genuine planner.attempt2.json exists."
    },
    {
      "id": "FIX-REPAIR-ARTIFACT-VALID",
      "pass": true,
      "evidence": "Code: the repair block computes 'let repair_artifact_valid = orchestrator.adapter.developer_artifact_valid(&workspace);' and uses it in the pushed AttemptOutcome. My plant (reverting that field to 'workspace.is_dir()'; restored byte-exact, sha256 97ba688529ccfeb2...0760) reddens tests/launchable_gate.rs::the_repair_attempt_artifact_validity_is_measured_not_assumed: exit 101, FAILED, panic at tests/launchable_gate.rs:564. The test pins both directions (repair leaves SCENE_WITHOUT_ROOT -> attempt 2 false; repair produces SCENE_WITH_ENTRY_SCRIPT plus a non-empty scripts/player.gd -> attempt 2 true), so neither hardcoded true nor hardcoded false passes."
    },
    {
      "id": "FIX-HARNESS-COMMAND-LINE",
      "pass": true,
      "evidence": "Code: 'DSH_TERM_CMD' joins HARNESS_ENV_VARS, and COMMAND_LINE_VARS + command_line_value_ends_at bound its value at the logical line end (physical CR/LF, the JSON \\n/\\r escape, or the unescaped closing quote) so ';', '&&', '>>', '\\\"' and '\\\\' are not terminators. My plant (removing the '    \"DSH_TERM_CMD\",' entry with a CRLF-aware anchor; restored byte-exact, sha256 6e9adf2f2162ba64...aed7) reddens runtime::secrets::tests::a_harness_command_line_does_not_leak_the_secret_file_it_names (exit 101, panic at src/runtime/secrets.rs:1354). A second plant run over all 19 secrets tests gives 17 passed / exactly the two new tests FAILED (the plain-text one AND the_real_json_command_line_shape_redacts_the_whole_value), so both pre-reds are assertion reds, not compile errors. The second test builds its fixture with serde_json::to_string (the real encoding), asserts the splice stays valid JSON, that </output> survives, and that bytes_changed_outside_spans == Some(0)."
    },
    {
      "id": "FIX-OUT-OF-TREE-BOUNDED",
      "pass": true,
      "evidence": "Code: hygiene.rs adds is_root_temporary (single path component AND .tmp_*/tmp_*/*.tmp/*.bak; rejects '.', '..', '', any separator, notes.tmp.bak.json, _probe.gd), clean_round_temporaries (iterates only the watcher's observed union, only is_file() direct children, re-checks path.parent()==root, returns the removed names, uses fs::remove_file - no wildcard, no directory removal, no rm), and OutOfTreeWatch::observed (the union, because observe()'s per-iteration return is consumed by the iteration record). run_loop.rs calls it at round close (:1845) and pushes 'out_of_tree_cleanup: removed N round-temporary file(s) from <root>: ...' into sweep_warnings, so it lands in warnings.log; the out_of_tree_writes record is kept. My plant (replacing the call with 'let cleaned: Vec<String> = Vec::new();'; restored byte-exact, sha256 97ba688529ccfeb2...0760) reddens tests/role_paths.rs::a_round_removes_its_own_root_temporary_and_records_it (exit 101, FAILED, panic at tests/role_paths.rs:529). The unit test asserts keep.txt, scenes/main.tscn, stray_dir/probe.txt and stray_dir/.tmp_nested.json all survive, and the pre-existing DR-25 test still requires stray_dir/probe.txt to remain on disk."
    },
    {
      "id": "GATE",
      "pass": true,
      "evidence": "My own `cargo test --offline` (offline, no engine, no round): 59 suites, 554 passed / 0 failed / 7 ignored, EXIT=0, zero 'FAILED' strings, zero error[. `cargo test --offline -- --list` yields 561 lines ending ': test', and all 8 new names are present (a_redacted_sidecar_is_not_a_second_attempt; the_repair_attempt_artifact_validity_is_measured_not_assumed; runtime::secrets::tests::{a_harness_command_line_does_not_leak_the_secret_file_it_names, the_real_json_command_line_shape_redacts_the_whole_value}; runtime::hygiene::tests::{only_root_level_temporary_shapes_are_round_litter, the_cleanup_removes_only_the_root_temporaries_the_watch_observed, the_watch_remembers_what_it_observed_across_the_round}; a_round_removes_its_own_root_temporary_and_records_it). 554+7 = 561 = the listing, consistent. REMOVED=0 is structural, not merely counted: the whole diff contains 6 removed lines, none of them a test function or a #[test]/#[tokio::test]/#[ignore] attribute, and 8 test attributes were added. `cargo fmt --check` exits 0 with empty output. Re-run after all six of my plants: EXIT=0, 554/0/7 - the tree was restored correctly."
    },
    {
      "id": "GATE-METHOD",
      "pass": true,
      "evidence": "All 96 tracked *.rs files carry the identical mtime 2026-10-02 06:33, which is what a per-file touch produces (and is only possible because the loop was driven from `git ls-files '*.rs'`, not a shell wildcard). The hof-rs rlib was rebuilt at 06:33:18 and test binaries at 06:33:22/06:33:49 (snapshot taken before my plant runs, which have since rebuilt them again). Zero target/debug/.fingerprint/hof-rs-* directories are older than 05:50 (oldest 05:55:56) over 60 directories - consistent with the claimed clearing at ~05:54 followed by the baseline build. Per-file rebuild therefore happened; the baseline count itself I did not re-run (see unverified)."
    },
    {
      "id": "WEAKER-RED-DISCLOSURE",
      "pass": true,
      "evidence": "Disclosed: the three hygiene unit tests' first red was a compile error, not an assertion failure. Verified: plant P5 renames 'pub fn is_root_temporary' and the lib test build fails with error[E0425]: cannot find function `is_root_temporary` in this scope x3, exit 101 (restored byte-exact, sha256 ceb84f3f756da6cd...b1fe). Weighing: the disclosure is accurate but it means only the role_paths integration test (my P4) is a true assertion-red for fix (1); the code path itself is well covered, so the weak red costs little - but a batch claiming strict TDD for four fixes should say plainly that one of the four had no assertion-driven first red, which it does."
    },
    {
      "id": "GUARDS",
      "pass": true,
      "evidence": "`find runs -type f -newermt '2026-10-02 05:52:00'` is empty (and stays empty after my two full suite runs and six plants); the newest file anywhere under runs/ is 05:23:00, so the batch and this acceptance wrote nothing there. `.workspace` has no file newer than 05:52. .spec/hof-rs/PRD-mario.md sha256 = 4c81c3a9995f0b3a...f0f5c3a. git show HEAD:DECISIONS.md sha256 = eb7090086c454966...548a7c2, identical to the value the T13 acceptance measured, and HEAD has 11,117 lines ending at D292 with no D293 - so the batch did not touch it (the working copy now differs only because a D293 entry was appended at 06:55:05 by the dispatcher, after this batch's close; the erratum's 'D293 does not exist' note was true of the frozen file). godot-mcp/godot HEAD = fc63af77c33368c4a1bb839c95d19750554f63a3 with an empty porcelain. Cargo.toml/Cargo.lock are not in the diff (no new dependencies). git status --porcelain has no D and no R (no tracked file deleted). 96 tracked .rs = 88 pure LF / 8 pure CRLF / 0 mixed, unchanged, and the one CRLF file this batch edited (src/runtime/secrets.rs) is still pure CRLF after my plants. origin/master is still 8ddbad3f... and `git diff --cached --name-only` is empty (nothing staged, nothing pushed)."
    },
    {
      "id": "MACHINE-BLOCK-ROUND-TRIP",
      "pass": true,
      "evidence": "TASK-DR79-REPORT.md has exactly one line-anchored ```json block (fences at lines 233 and 432). json.loads -> 14 top-level keys; json.dumps(obj, ensure_ascii=False, indent=2) reproduces the block text exactly (10,399 UTF-8 bytes), which is also byte-equal to the implementer's own C:\\Users\\wyl\\AppData\\Local\\Temp\\dr79\\block.json - i.e. it was serialised and read back, not handwritten. Its fields match my independent measurements: head 4c8e76a8..., origin_master_at_close 8ddbad3f..., pushed false, erratum {318 insertions, 0 deletions, head_file_bytes 107703, appended_bytes 26376, prefix_bytes_identical_to_head true}, gate.baseline {546/0/7, 59 suites, 553 listed}, gate.final {554/0/7, 59 suites, 561 listed}, corrections T13A-1..9, four fixes, eight residual risks."
    },
    {
      "id": "PRE-EXISTING-TMP-FILES-PRESERVED",
      "pass": true,
      "evidence": "The three untracked root temporaries are still present with unchanged mtimes: .tmp_coin.json 108 B at 04:52:28.970, .tmp_goal.json 68 B at 04:52:29.061, .tmp_hud.json 46 B at 04:52:29.124 (none tracked, all listed in result.json.out_of_tree_writes = ['.tmp_coin.json','.tmp_goal.json','.tmp_hud.json']). They are outside the cleaner by construction: clean_round_temporaries acts only on paths the round's own watcher observed change, and they pre-date any future round. Deliberately preserving them is the right call - they are T13's forensic objects - and the report says so."
    }
  ],
  "defects": [
    {
      "id": "D-1",
      "severity": "minor",
      "what": "The new material misstates the two round-author probe reply sizes. Erratum E-1 (TASK-SMOKE-T13-REPORT.md line 1548) and TASK-DR79-REPORT.md line 36 say 'tools/list (25,908 B reply)' and 'running_game_get_scene_tree (816 B)'. The measured reply payloads are 31,202 B and 589 B; the FILE sizes are 31,360 B and 816 B. So 816 is the file size rather than the reply, and 25,908 matches no artifact at all (file size, reply, json.dumps(result), json.dumps(result, separators tight), json.dumps(tools) = 31,360 / 31,202 / 41,024 / 39,346 / 39,336; `find runs/smoke-t13 -type f -size 25908c` -> nothing). The substantive claim (both probes addressed :53068 and returned valid replies) is true, so no mechanism conclusion moves - but a fresh wrong number in a batch whose whole point is that numbers must recompute from the cited record is exactly the class of error it was correcting.",
      "reproduction": "python: b = open('runs/smoke-t13/evidence/round/game_endpoint_tools_list_round_author.json','rb').read(); s = b.find(b'---- raw reply begin ----') + 25; e = b.find(b'---- raw reply end ----'); print(len(b), len(b[s:e].rstrip(b'\\n')))  ->  31360 31202 ; same for game_endpoint_scene_tree_round_author.json -> 816 589 ; sha/ls the files for the file sizes."
    },
    {
      "id": "D-2",
      "severity": "minor",
      "what": "The corrected evidence-index row still carries a stale sha256. The report's index (line 1485) lists cite_check.txt as 18,189 B / sha256-prefix 4bbce1a00a26101c; erratum E-4e corrects the size to 18,401 but explicitly left the hash unchecked and reprinted 4bbce1a00a26101c. The actual sha256 is 21f071f5e0c7ef5ee7374848293f2297f3270207a6bf046b88d97fd506ab455a. The neighbouring rows are accurate (e.g. machine_block.json 34,699 / 36e34d0d04369206 recomputes), so the convention is right and only this row is stale in both columns - the erratum repaired one column. Disclosed as unverified by the author, so this is an incomplete correction rather than a false claim, but the frozen document now pairs a correct size with a wrong hash.",
      "reproduction": "sha256sum runs/smoke-t13/evidence/analysis/cite_check.txt  -> 21f071f5e0c7ef5e... (18,401 B); grep -n 'cite_check.txt' .spec/hof-rs/tasks/TASK-SMOKE-T13-REPORT.md -> line 1485 lists 18189 / 4bbce1a00a26101c and line 1691 repeats it as 'unchecked'."
    },
    {
      "id": "D-3",
      "severity": "low",
      "what": "Nothing mechanical protects the append-only property of the historical report. No test, script or hook in the repository mentions TASK-SMOKE-T13-REPORT.md (grep over *.rs and *.py: 0 matches), and core.hooksPath points at .githooks, which contains only the DR-75 pre-push acceptance-ledger gate (it authorises commits, it does not compare report text). My plants show the property is only caught by a reviewer who chooses to run `git diff --numstat` or compare the working file's prefix with the HEAD blob. Because the HEAD blob is in git, the check is always reproducible - but it is discipline, not a gate. Precedent exists for making it mechanical (tests/byte_claims.rs pins TASK-DR70-REPORT.md, tests/dr77_evidence_tightening.rs pins TASK-DR73-REPORT.md).",
      "reproduction": "grep -rn 'SMOKE-T13-REPORT' --include=*.rs --include=*.py . -> no matches; git config --get core.hooksPath -> .githooks; ls .githooks -> README.md, hoh-acceptance-lib.sh, pre-push. Plant on a temp copy of the report: edit one original-region line -> anything that does not run the git comparison sees nothing."
    },
    {
      "id": "D-4",
      "severity": "info",
      "what": "Not a defect of this batch, but a downstream trap it leaves in place: the frozen analysis product runs/smoke-t13/evidence/analysis/round_facts.txt:160 itself carries the wrong split 'execution records: verified-only = 10, gap-only = 13, verified+gap = 31' that the report inherited. The erratum corrects the report (21/10) and correctly leaves the frozen artifact byte-unchanged, so anyone reading round_facts.txt still gets 10/13. The erratum cites round_facts.txt:161 (record types) as corroboration but does not flag :160 as the origin of the error.",
      "reproduction": "sed -n '160p' runs/smoke-t13/evidence/analysis/round_facts.txt ; python: ev=json.load(open('runs/smoke-t13/iter-1/evidence.json')); sum(len(r['execution_records']) for r in ev['verified_records'])=21, for gap_records=10."
    }
  ],
  "risks": [
    "The DR-70 attribution to the 04:41:38 repair restart is a reconstruction from indirect artifacts (warnings.log's size/mtime decomposition, the Godot user://logs rotation timeline, and HEAD's call-site order). It is much stronger than the report's own 'strong inference' - four known port facts (:53068 round start, :55336 pass 1, :55361 repair, :51223 pass 2) fit the log timeline with no residue - but the harness still emits no per-start record (attempt number, endpoint, poll count, outcome). Until it does, every future round's T13A-1-class question will again be an inference.",
    "D-1/D-2 (and round_facts.txt:160) stay frozen unless a follow-up additive erratum corrects them; append-only means a wrong number, once pushed, can only be superseded, never repaired in place.",
    "clean_round_temporaries deletes files that the round's own watcher observed as changed, so a PRE-EXISTING root temporary that the round happens to touch (not create) becomes eligible. The blast radius is bounded to single-component .tmp_*/tmp_*/*.tmp/*.bak direct children, and out_of_tree_writes keeps the record, so the exposure is small - but 'pre-existing' is not by itself proof of safety.",
    "The cleanup is root-only and single-component by design: nested temporary files, and temporaries written after the last observe() (the tester's window ends at run_loop.rs:1668, the round-close cleanup runs at :1845), remain report-only.",
    "Roles still inherit DSH_TERM_CMD; DR-79 only adds a redaction rule for the NAME=value shape in artifacts produced from now on. The frozen T13 trajectories still contain the readable command line (read-only by design), and a bare value with no NAME= prefix is still uncovered.",
    "The new usage filter is a substring test on '.redacted.' rather than the secrets module's REDACTED_COPY_SUFFIX constant (which the doc comment on the same function links to). It is correct today for DR-72's '<name>.redacted.json' shape, but the two notions of 'redacted copy name' can drift."
  ],
  "unverified": [
    "I did not build or run the suite at HEAD, so the baseline reading 546 passed / 0 failed / 7 ignored / 553 listed is not independently reproduced. What I verified is the delta: the diff removes 6 lines, none of them a test or a test attribute, and adds 8 test attributes; the final run is 554/0/7 with 561 listed and all 8 new names present, so 546/553 follow arithmetically and REMOVED=0 is structural. A HEAD-build run would close this.",
    "The implementer's intermediate history is corroborated but not observed by me: the launchable_gate fixture bug (SCENE_WITH_ROOT not satisfying developer_artifact_valid), P3's first anchor missing on a LF anchor in a CRLF file, and the number of removed fingerprint directories. Their temp material is consistent (two identical P3 backups, sha 6e9adf2f...; clear_fp.py enumerating with shutil.rmtree; block.json byte-equal to the report block), and my own P3 used a CRLF anchor successfully, but I did not witness the failed attempts.",
    "The DR-70 code-order argument is a reconstruction: I did not instrument the engine, and the round was not re-run (forbidden). The Godot-log timeline is my strongest independent evidence and it depends on the rotation convention that each godot<timestamp>.log holds the session that preceded the process start at that timestamp; it fits all four known ports, but I did not read the engine's logger source to prove the convention.",
    "I re-verified only the cite_check.txt row of the 59-row evidence index (and the machine_block.json row); the other rows' sizes and sha prefixes were not recomputed.",
    "I did not diff the four *.redacted.json sidecars against their originals, and did not re-derive the six T13 acceptance criteria E1..E6, the A0/A1 tree digests, the ten read-only baselines or the tool census - all out of this batch's scope.",
    "I cannot verify the implementer's negative claims about their own commands (no rm -rf, no unexpanded-variable path construction, no PowerShell raw read+write pair, no whole-file EOL rewrite). I verified the effects I can see: no tracked file removed, no line-ending change (88 LF / 8 CRLF / 0 mixed, before and after my own plants), and their helper scripts contain no rm -rf and use enumerated shutil.rmtree only for target/debug/.fingerprint/hof-rs-*."
  ],
  "not_checked": [
    "No engine start, no round, no network: the whole acceptance ran offline, and I wrote nothing under runs/** (not even a temporary file).",
    "I did not modify the frozen report, DECISIONS.md, any workspace, the PRD, godot-mcp/** or the root .tmp files; the six plants were applied to src/tests with byte backups outside the repository and every one was restored byte-exactly (sha256 compared) before the next step.",
    "I did not push, stage, commit, create a branch or use rm -rf; temporary material lives in C:\\Users\\wyl\\AppData\\Local\\Temp\\dr79acc.",
    "I did not re-run the T13 round or re-derive its criteria; I did not inspect godot-mcp/** or the engine binary."
  ],
  "plants_and_counterexamples": [
    "Additivity plant A (in-place edit of one original-region prose line, temp copy only): prefix_identical_to_HEAD False, 1 changed line -> caught by the git diff / prefix check.",
    "Additivity plant B (delete one original-region line): prefix False, 1 deletion -> caught.",
    "Additivity plant C (edit inside the json block): prefix False AND the machine-block byte comparison against machine_block.json False -> caught by two checks; note that a tamper inside the block alone leaves a plain `git diff` looking like a 1-line change, so the byte-identity check is the load-bearing one.",
    "P1 usage filter (delete '&& !name.contains(\".redacted.\")'): usage_extraction::a_redacted_sidecar_is_not_a_second_attempt FAILED, exit 101; restore sha 0014353268346efb...9499.",
    "P2 repair artifact_valid (repair_artifact_valid -> workspace.is_dir()): launchable_gate::the_repair_attempt_artifact_validity_is_measured_not_assumed FAILED, exit 101; restore sha 97ba688529ccfeb2...0760.",
    "P3/P6 harness command line (delete the 'DSH_TERM_CMD' list entry, CRLF anchor): P3 reddens the plain-text test alone; P6 runs all 19 secrets tests -> 17 passed / exactly the two new tests FAILED, proving both new tests were assertion-red before the fix; restore sha 6e9adf2f2162ba64...aed7.",
    "P4 cleanup wiring (call -> 'let cleaned: Vec<String> = Vec::new();'): role_paths::a_round_removes_its_own_root_temporary_and_records_it FAILED, exit 101; restore sha 97ba688529ccfeb2...0760.",
    "P5 weak-red proof (rename 'pub fn is_root_temporary'): error[E0425] x3, exit 101 -> the disclosed compile-error red is real; restore sha ceb84f3f756da6cd...b1fe.",
    "Counterexample to E-1's reply sizes: the file/reply decomposition 31,360/31,202 and 816/589, plus a repository-wide search that finds no 25,908-byte file.",
    "Counterexample to the acceptance's screenshot:2 sub-claim: report line 296 at HEAD and at commit 62ad5a0 both list all five record types summing to 31, and evidence.json recomputes to the same five - so the sub-claim fails at every revision, not merely at a stale one.",
    "Endpoint-attribution cross-check: pass 1's own play_scene_ready (quarantine) answers :55336 while the DR-70 line names :55361, so the failing start cannot be pass 1's; and the two banner-only Godot session logs (199 B) correspond exactly to the two starts known to have failed.",
    "Independence check on the machine block: json.loads + json.dumps(ensure_ascii=False, indent=2) reproduces the block byte-for-byte, and the block is byte-equal to runs/smoke-t13/evidence/analysis/machine_block.json - so the original machine-readable record really was left alone."
  ]
}
```

<!-- DR79-ACCEPTANCE self-check: the block above was produced by json.dumps(obj, ensure_ascii=False, indent=2)
     and read back with json.loads before this file was written (see the generator script, out of repo). -->

# TASK-DR79-ACCEPTANCE — independent acceptance

Independent acceptance subagent; no upstream context; offline; **no round executed, no engine started, `runs/**` read-only**.
Every number below was produced by my own commands or by reading the raw artifacts; `TASK-DR79-REPORT.md` was used only as a lead.

## 0. Verdict

| item | my verdict | one-line basis |
|---|---|---|
| Additivity of the erratum | **pass** | `318 / 0`; HEAD blob 107,703 B is a byte-identical prefix of the 134,079 B working file; appended 26,376 B; the json block is byte-identical to `machine_block.json` (34,699 B) |
| Additivity under tampering | **pass, but nothing mechanical catches it** | my three plants are caught by `git diff --numstat` / prefix comparison / block byte-identity — all reviewer-run; no test or hook reads the file (`D-3`) |
| T13A-1 (initial start succeeded; DR-70 = repair restart) | **pass** | two probes addressed `:53068` (staging mtimes 04:19:22.644/.842) + msg 77 `configured_port=53068` + `warnings.log` 1,110 B at 04:41 + HEAD `:1343→:1348` guarded by the failed gate |
| T13A-1 (refusal time; narrowed risk) | **pass** | msgs 137/138/139 ts 1790887888.17 = 04:51:28 by the `epochs.txt` anchors; E-1 items 4/5/6/7 narrow exactly what the task book required |
| T13A-2 (64 KiB fired once) | **pass** | `tester.attempt1` msg 98, 65,536 / 81,139, ts 04:56:37, runtime marker verbatim; exactly one hit in four trajectories |
| T13A-3 (real attribution) | **pass** | HEAD `:1137/:1147/:1154/:1185` is the wrap-up block (`wrap_up_retry_used=false`); `:1378` is `workspace.is_dir()` |
| T13A-4 sub-item refused | **pass (refusal was right)** | line 296 lists 5 record types summing to 31 at HEAD and at the earlier commit; the acceptance’s own `reproduction` prints `screenshot:2` |
| Fix ① out-of-tree writes | **pass** | my P4 reddens the wiring test; rule + bidirectional pins verified; nested/non-temp paths untouched |
| Fix ② usage double count | **pass** | my P1 reddens the sidecar test; old filter picks 2 planner files, new picks 1; frozen summary is exactly 2× the attempt |
| Fix ③ `artifact_valid` | **pass** | my P2 reddens the test; both directions pinned |
| Fix ④ command-line redaction | **pass** | my P3/P6 redden the two new tests (17 old ones stay green); real-JSON fixture |
| Gate | **pass** | mine: 59 suites, **554 / 0 / 7 ignored**, exit 0, `--list` 561, 0 test removed, `fmt --check` 0, re-run after plants still 554/0/7 |
| Gate method (fingerprints + per-file touch) | **pass** | all 96 `.rs` share mtime 06:33; rlib rebuilt 06:33:18; no `hof-rs-*` fingerprint older than 05:50 |
| Disclosed weaker red | **pass (accurate, and cheap)** | P5 shows the hygiene unit tests fail to compile without the functions; only the integration test is a true assertion-red |
| Guards | **pass** | `runs/**` and `.workspace` untouched; PRD/`DECISIONS.md`(HEAD)/engine/Cargo untouched; no deletion; 88 LF / 8 CRLF / 0 mixed; no new deps; not pushed/staged |
| Machine-readable block | **pass** | 1 block, `json.loads` → 14 keys, `json.dumps(..., indent=2)` reproduces it byte-for-byte, fields match my measurements |
| Root `.tmp_*.json` preserved | **pass** | 108/68/46 B, mtimes 04:52:28–29, untracked, outside the cleaner’s observed-only scope |

**Overall: pass.** All six mandated job areas reproduce. Two minor numeric defects live in the *new* appended text (D-1 probe reply sizes; D-2 a stale sha in the corrected index row) and one repository-wide gap is exposed (D-3 no mechanical append-only guard). None contradicts a mechanism claim, so I do not fail the batch — but D-1/D-2 should be fixed by a small additive follow-up before the next real round, and D-4 (a frozen analysis product that still carries the wrong 10/13 split) should be registered at the same time.

## 1. Per-item evidence table (detail)

See the `criteria` array above for the full evidence strings. Summary of the exact commands I ran:

| # | check | my command / read | result |
|---|---|---|---|
| 1 | erratum size | `git diff --numstat -- .spec/hof-rs/tasks/TASK-SMOKE-T13-REPORT.md` | `318 0` |
| 2 | prefix identity | `git show HEAD:… > head.md`; byte-compare | 107,703 B prefix identical; +26,376 B appended |
| 3 | machine block | line-anchored fence scan + `json.loads` + byte-compare with `machine_block.json` | 1 block, 29 keys, identical (34,699 B, `36e34d0d04369206`) |
| 4 | probe endpoints | first line of the two `game_endpoint_*_round_author.json`; staging `stat` | `POST http://127.0.0.1:53068/mcp`; mtimes 04:19:22.644/.842 |
| 5 | round-start route | `developer.attempt2.json` msgs 70–78 (`extra.actions`, `extra.timestamp`) | msg 77 reads `configured_port=53068` at 04:44:02.75 |
| 6 | Godot session timeline | `ls`/`cat` of `%APPDATA%\Godot\app_userdata\HoH Mario\logs` | `:53068` log rotated at 04:41:23; two banner-only logs (04:41:38, 04:54:38); `:51223` at 04:54:50 |
| 7 | `warnings.log` | byte read + msg 135 `dir` tail | 1,849 B / 7 LF now; 1,110 B at 04:41 = 212 + 896 + 2 |
| 8 | refusal time | msgs 137–139 `extra.timestamp` + `epochs.txt` | 1790887888.17 → 04:51:28 |
| 9 | truncation | parse `extra.hoh_output_truncated` over 4 trajectories | 1 hit, msg 98, 65,536/81,139 |
| 10 | `artifact_valid` | HEAD `run_loop.rs` grep + `result.json` | 1137/1147/1154/1185 wrap-up (did not fire); 1378 always-true |
| 11 | counts | `evidence.json`, `find … | wc -l`, `sha256sum` | 21/10/31; 268/110/23/31/5/51/158; `cite_check.txt` 18,401 B |
| 12 | record types | report line 296 (HEAD and `62ad5a0`) + `round_facts.txt:161` | 5 families summing to 31 — the refused sub-item does not exist |
| 13 | leak | grep over 268 files + 51-byte key scan | `DSH_TERM_CMD` in 4 files ×2; key value 0 hits |
| 14 | gate | `cargo test --offline`; `-- --list`; `cargo fmt --check` | exit 0; 554/0/7; 561; 0 removed; fmt 0 |
| 15 | guards | `find -newermt`, `git status`, `sha256sum`, nested `git -C` | all clean, not pushed, nothing staged |

## 2. My own plants and counterexamples

Each plant was applied to the real `src/**` or `tests/**` file with a byte backup kept outside the repository, ran the one intended test, and was restored and re-hashed before anything else happened. All six restored byte-exactly:

| plant | broken form | intended test | result | restore |
|---|---|---|---|---|
| P1 | delete `&& !name.contains(".redacted.")` | `a_redacted_sidecar_is_not_a_second_attempt` | exit 101, `FAILED`, panic at `tests/usage_extraction.rs:121` | `0014353268346efb…9499` (identical) |
| P2 | `repair_artifact_valid` → `workspace.is_dir()` | `the_repair_attempt_artifact_validity_is_measured_not_assumed` | exit 101, `FAILED`, panic at `tests/launchable_gate.rs:564` | `97ba688529ccfeb2…0760` |
| P3 | delete the `"DSH_TERM_CMD",` entry (CRLF anchor) | `a_harness_command_line_does_not_leak_the_secret_file_it_names` | exit 101, `FAILED`, panic at `src/runtime/secrets.rs:1354` | `6e9adf2f2162ba64…aed7` |
| P4 | `clean_round_temporaries(…)` → `let cleaned: Vec<String> = Vec::new();` | `a_round_removes_its_own_root_temporary_and_records_it` | exit 101, `FAILED`, panic at `tests/role_paths.rs:529` | `97ba688529ccfeb2…0760` |
| P5 | rename `pub fn is_root_temporary` | the hygiene unit tests | `error[E0425] ×3`, exit 101 (compile red, as disclosed) | `ceb84f3f756da6cd…b1fe` |
| P6 | same as P3, but run all `runtime::secrets::tests` | 19 tests | **17 passed, exactly the 2 new ones FAILED** → both pre-reds are assertion reds | `6e9adf2f2162ba64…aed7` |

Additivity plants (temp copies of the report only): an in-place prose edit and a line deletion both break the HEAD-prefix check and show up as deletions in a line diff; an edit inside the json block also breaks the byte comparison with `machine_block.json`. The finding is that all three checks are things a human runs — nothing in the repository runs them (`D-3`).

Counterexamples I constructed beyond the brief:

- **Probe reply sizes.** Treating the two evidence files as files gives 31,360 and 816 B; treating their payload as replies gives 31,202 and 589 B. The erratum’s “25,908 / 816 B” is a mix of neither, and no 25,908-byte file exists anywhere under `runs/smoke-t13` (`D-1`).
- **`screenshot:2` at every revision.** Line 296 of the report at HEAD *and* at the first T13 report commit `62ad5a0` both carry the five-family table; the acceptance’s own `reproduction` field prints `screenshot:2`. So the refused sub-item is not a stale-file artefact — it never existed.
- **Two failed starts, two banner-only logs.** The Godot session logs contain exactly two 199-byte banner-only sessions, and the round contains exactly two starts known to have failed readiness (pass 1 on `:55336`, the repair restart on `:55361`). Four known ports (`:53068`, `:55336`, `:55361`, `:51223`) all land on the expected sessions.
- **Stale hash.** `cite_check.txt` recomputes to `21f071f5e0c7ef5e…`, not the index’s `4bbce1a00a26101c`, while `machine_block.json` and the neighbouring rows recompute exactly — so the index convention is sound and only this row is stale (`D-2`).

## 3. Independent judgement

1. **The additivity rule was honoured literally.** `318 / 0`, a byte-identical 107,703-byte prefix, and a machine-readable block that is byte-equal to the round’s own `machine_block.json`. The erratum’s own E-9 is the right shape: it names the superseded machine-block fields, leaves them verbatim, and says where the authoritative reading now is. This is the strongest part of the batch.
2. **All three mechanism corrections are right, and one of them I could strengthen.** The report’s “initial start failed at 04:17:44” is contradicted by the probes, by `configured_port=53068`, by the `warnings.log` size decomposition, and — new here — by the Godot user-data log timeline, which shows the `:53068` session living from ~04:17:47 and the `:55361` session being the 04:41:38 restart that never bound. The 64 KiB claim is flatly inverted in the original and the erratum fixes it and registers it as the first real-machine exercise. `artifact_valid`’s :1378 attribution is correct and provably so from HEAD.
3. **The refusal was the right call and is well argued.** E-7 quotes the actual line, the frozen analysis product, and the absence of a record-type key in the machine block, and it says plainly that this is an independent judgement on the acceptance rather than a defence of the report. I verified each leg.
4. **The four fixes are real, tested and pinned.** My own plants redden exactly the intended tests in each case and restore byte-exactly, which is the only way to distinguish a test that guards the fix from one that merely runs alongside it. The bidirectional pins matter: the usage fix cannot pass by ignoring every file, the artifact-valid fix cannot pass by hardcoding `false`, the cleanup cannot reach project content, and the command-line rule is exercised in the real JSON encoding.
5. **The gate is genuine and self-consistent.** 554 + 7 = 561 = the listing, no test removed, `fmt` clean, and the “per-file touch” claim is visible in the filesystem (all 96 `.rs` at the same minute, rlib rebuilt 06:33:18, no stale `hof-rs-*` fingerprint). My post-plant re-run is still 554/0/7, so the plants did not leave damage.
6. **But the batch’s own standard slips twice in its new text.** A batch whose thesis is “every number must recompute from the artifact it cites” appends “25,908 B” for a reply that is 31,202 B (and “816 B” for one that is 589 B), and repairs the size column of an index row while leaving its hash column wrong. Neither changes a conclusion; both would be embarrassing if a later acceptance read the erratum as the authoritative record. I record them as minor defects rather than failing the batch because the mechanism claims, which is what the acceptance was actually about, all hold — but a follow-up additive erratum is the right closure, and I would not push without deciding explicitly whether to accept them as-is.
7. **The residual-risk list is honest and I found nothing hidden in it.** I verified every item I could: the three `.tmp` files are still there with unchanged mtimes, the key value really is absent (0 hits over 268 files), `DSH_TERM_CMD` really is still in the four frozen trajectories, the cleaner really is root-only, the `dotted` filter really is a literal rather than the `REDACTED_COPY_SUFFIX` constant it links to. The only item that changes status is the `cite_check.txt` hash — the author said it was unchecked, and it turns out to be stale (`D-2`).

## 4. Unverified items and what I did not check

See the `unverified` and `not_checked` arrays in the block above. The two that matter most:

- **The HEAD baseline (546/0/7, 553 listed) is not reproduced**, because building at HEAD would mean a second full build and I judged the structural argument sufficient: the diff removes no test and adds exactly 8 test attributes, and the final listing contains all 8 new names, so 554 − 8 = 546 and 561 − 8 = 553. A stricter acceptance would build HEAD in a scratch clone and diff the two `--list` outputs; I did not.
- **The engine was not instrumented**, so the DR-70 attribution remains a reconstruction. My Godot-log timeline is independent evidence, not a harness record; the next batch should add per-start logging rather than repeat this deduction.

## 5. Advice for the next batch

1. **Ship a two-line additive erratum** for `D-1` (31,202 B / 589 B, with the file sizes named separately) and `D-2` (`cite_check.txt` sha256 = `21f071f5e0c7ef5e…`), and register `D-4` (`round_facts.txt:160` still says 10/13) as a known-stale frozen product. Do not touch the existing text — append.
2. **Make the append-only rule mechanical.** There is precedent in this repository: `tests/byte_claims.rs` pins `TASK-DR70-REPORT.md` and `tests/dr77_evidence_tightening.rs` pins `TASK-DR73-REPORT.md`. A test that reads `git show HEAD:.spec/hof-rs/tasks/TASK-SMOKE-T13-REPORT.md`, asserts the working file’s prefix is byte-identical, and asserts the json block is byte-identical to `machine_block.json` would turn `D-3` from discipline into a gate, and would generalise to every future erratum.
3. **Instrument `start_round_game`.** One line per call — attempt number, chosen endpoint, poll count, outcome — into the round’s own record would have settled T13A-1 directly and would retire the entire class of inference. Until then, keep writing these attributions down as reconstructions with their evidence.
4. **Give the temporary cleaner a wider account.** It currently records only what it removed. Consider also recording pre-existing temporaries that were observed but left alone, so the “pre-existing is never touched” claim becomes a reading rather than a promise.
5. **Decide about `DECISIONS.md` deliberately.** D293 was appended by the dispatcher at 06:55:05 (after this batch closed); HEAD still ends at D292. Its content agrees with my measurements. If it stays, the erratum’s “D293 does not exist” line is a statement about the frozen file at the time, which is accurate — but the next erratum should say so explicitly rather than leave two entries that appear to contradict each other.

---

*Method note: the structured block at the top of this file was produced with `json.dumps(obj, ensure_ascii=False, indent=2)` from a generator script kept outside the repository, written to disk, then read back and `json.loads`-ed as a final check. Plants were applied to `src/**`/`tests/**` only, always with byte backups outside the repository, and every file was restored to its pre-plant sha256 before the next step; a full suite re-run afterwards is 554 passed / 0 failed / 7 ignored, exit 0.*