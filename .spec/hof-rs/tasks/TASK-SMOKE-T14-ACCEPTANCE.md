```json
{
  "verdict": "pass",
  "criteria": [
    {
      "id": "H1-EXIT-CODE",
      "pass": true,
      "evidence": "runs/smoke-t14/exit_code = bytes 36 0A; process_exit_code = bytes 36 0A; meta.json.exit_code = 6; round_console.txt ROUND_EXIT: 6. Four readings agree, value 6. result.json.artifact_gate = {applicable:true, launchable:false}."
    },
    {
      "id": "H2-GATE-REASONS",
      "pass": true,
      "evidence": "artifact_gate.reasons has exactly one entry: 'editor_errors_baseline: editor reported 1 error(s): {\"available\":true,\"count\":1,...,\"errors\":[\"  ERROR: Cannot create file 'res://.godot/editor/filesystem_cache10'. Check user write permissions.\"],...} (UNAVAILABLE: the editor is not clean; 1 line(s) still reproducible)'. The only res:// token in it is the .godot/editor cache path (a path the runtime excludes from hashing and snapshots) - nothing in the produced project. Independently, iter-1/candidate/.hoh/deterministic/raw/editor_errors_baseline.json (pass 2) carries exactly that one line, count=1."
    },
    {
      "id": "H3-GATE-CANNOT-DISTINGUISH",
      "pass": true,
      "evidence": "src/adapter/mod.rs:41-73 evaluate_launchable: launchable = every declared GATE_STEP_ID ok (editor_errors_baseline, play_scene_ready, engine_identity). src/adapter/godot.rs:795-889 step_editor_errors: ok=true only when the errors array is empty, when every line is an exact [MCP] banner (DR-48), or when every line is a stale editor-log line whose res://file:line no longer contains the quoted symbol it names (DR-68, godot.rs:5243-5279). A cache-write line that names res://.godot/... is neither, so it closes the gate. The gate's other mandatory step is green (play_scene_ready ok, 22 nodes, 1 poll) and engine_identity ok, so the two mandatory steps disagree: 'the project boots and answers' vs 'the editor log has a non-banner line'."
    },
    {
      "id": "H4-NOT-PERMISSIONS",
      "pass": true,
      "evidence": "icacls .workspace\\fresh-t14\\.godot and .workspace\\fresh-t13\\.godot are line-for-line identical (Authenticated Users:(I)(M), Users:(I)(RX), Administrators/SYSTEM (I)(F)). The engine's 'Check user write permissions' is generic wording."
    },
    {
      "id": "H5-NOT-UNIVERSAL",
      "pass": true,
      "evidence": "evidence/analysis/godot_editor_dir_check.txt (re-read by me): .godot/editor/filesystem_cache10 exists in mario 1241 B, fresh-t11 673 B, fresh-t12 805 B, fresh-t13 789 B; fresh-t14 has no .godot/editor directory at all. I re-listed all five directories myself."
    },
    {
      "id": "H6-REAL-SCRIPT-ERROR-WAS-DETECTED-AND-FIXED",
      "pass": true,
      "evidence": "quarantine/deterministic-pass-1.stale-1790906763/raw/editor_errors_baseline.json: count=6 including 'ERROR: res://scripts/main.gd:8 - Parse Error: Expected new line after \\\"\\\\\\\".' and 'Failed to load script \"res://scripts/main.gd\" with error \"Parse error\"'. Pass 2 (candidate raw payload) has count=1 = only the cache line. developer.attempt2.log notes = 'launch_gate_repair: the pre-freeze launchable gate failed'; result.json repair_retry_used=true, wrap_up_retry_used=false. So the gate did detect a genuine script error and the repair removed it."
    },
    {
      "id": "H7-GATE-INPUT-UNSTABLE",
      "pass": true,
      "evidence": "evidence/round/live_editor_get_errors.json: a later editor_get_errors call against the same editor (pid 36808, port 9877) returns count=1 with the single line '[MCP] capture=off (default; use --mcp-capture=on_error|every_call together with --mcp-trace=<path>)' - a line that is not an error and that DR-48 would exempt. Same project, same process, different verdict 48 minutes later."
    },
    {
      "id": "H8-SCRIPT-DETECTION-MUST-SURVIVE-A-FIX",
      "pass": true,
      "evidence": "The blunt predicate is the only thing that caught res://scripts/main.gd:8 in pass 1 (editor_error_is_stale returns false for a line without a quoted \"X()\" symbol, godot.rs:5243-5259, so parse errors are kept). Any fix that exempts the cache-write line must add a specific, additive exemption; relaxing the predicate would silently stop detecting real script errors."
    },
    {
      "id": "R1-DSH-TERM-CMD-SURVIVES",
      "pass": true,
      "evidence": "Counts I produced myself over the frozen sidecars: developer.attempt1.redacted.json DSH_TERM_CMD=cd 4, DSH_TERM_CMD=<redacted> 0; developer.attempt2.redacted.json 2 / 0. The surviving text is the round author's harness command line, e.g. 'DSH_TERM_CMD=cd /f/moonbit-hof-rs && python \\\"F:/moonbit-hof-rs-t14-staging/scripts/run_stream.py\\\" --out ... --env-from-secret HOH_MODEL_API_KEY -- ...'."
    },
    {
      "id": "R2-HOH-GAME-ROUTE-SURVIVES",
      "pass": true,
      "evidence": "HOH_GAME_ROUTE=F:\\\\moonbit-hof-rs\\\\runs\\\\smoke-t14\\\\game_endpoint.json appears raw 4/4 in developer.attempt1[.redacted].json and 4/4 in developer.attempt2[.redacted].json; HOH_GAME_ROUTE=<redacted> appears 0 times anywhere."
    },
    {
      "id": "R3-OTHER-NAMES-REDACTED-IN-THE-SAME-DUMP",
      "pass": true,
      "evidence": "Same sidecars: HOH_MODEL_API_KEY=<redacted> 4 in attempt1 and 4 in attempt2; PATH=<redacted> 2 and PSMODULEPATH=<redacted> 1 in attempt1 (PSMODULEPATH matches the 'PATH=' needle as a substring); in attempt2 HOH_ROLE/HOH_RUN_DIR/HOH_RUN_ID/HOH_SCRATCH_DIR/HOH_TOOLS_ENDPOINT/HOH_VIEW_DIR each get exactly 1 <redacted> where attempt1 gets 0. Total <redacted> markers 7 (attempt1) and 10 (attempt2), matching result.json.secret_redactions=7 for the copies the report names and the redaction_pairs.txt span list."
    },
    {
      "id": "R4-SECRET-VALUE-ABSENT",
      "pass": true,
      "evidence": "I read config/model.secret.env myself (no printing) and scanned all 391 files under runs/smoke-t14 and .workspace/fresh-t14 for the 51-byte HOH_MODEL_API_KEY value: 0 hits."
    },
    {
      "id": "R5-MECHANISM-UNDETERMINED-IS-INCOMPLETE",
      "pass": true,
      "evidence": "The report's F-T14-2 says the mechanism is undetermined. I determined it and reproduce it: a faithful byte-level port of splice_assignments (src/runtime/secrets.rs:311-363) reproduces BOTH real sidecars byte-for-byte from their originals, with spans {HOH_MODEL_API_KEY:4, OPENAI_API_KEY:1, PATH:2} = 7 and {HOH_MODEL_API_KEY:4, HOH_ROLE/RUN_DIR/RUN_ID/SCRATCH_DIR/TOOLS_ENDPOINT/VIEW_DIR:1 each} = 10. Root cause: the guard 'if spans.iter().any(|span| start < span.end)' (secrets.rs:324) is not an overlap test but a global 'start precedes the largest span end so far' test; because one trajectory contains the same environment dump several times, a later-scanned variable's late occurrence (OPENAI_API_KEY at 286080-286095) blocks every earlier occurrence of every name scanned afterwards (all HOH_*, DSH_TERM_CMD, most PATH occurrences)."
    },
    {
      "id": "R6-THE-PASSING-UNIT-TEST-IS-INSUFFICIENT-BY-CONSTRUCTION",
      "pass": true,
      "evidence": "The two DR-79 (4) tests (src/runtime/secrets.rs:1348-1376 and :1384-1416) call the same public helper but on fixtures with exactly one assignment and no repeated dump; my port redacts both fixtures correctly. A minimal plant proves the insufficiency: text with a DSH_TERM_CMD line followed later by 'OPENAI_API_KEY=' leaves DSH_TERM_CMD raw, while deleting that one later assignment makes the identical DSH_TERM_CMD line redact. Under the guard, a later position for a name scanned earlier always wins."
    },
    {
      "id": "B1-PROBE-REALLY-ISSUED-A-SCENE-PLAY",
      "pass": true,
      "evidence": "evidence/probe/role_play_probe3.txt: COMMAND_VERBATIM 'F:\\moonbit-hof-rs\\target\\release\\hoh.exe tools call editor_play_scene --args-file ... --role developer', HOH_ROLE=developer, HOH_GAME_ROUTE=F:\\moonbit-hof-rs\\runs\\smoke-t14\\game_endpoint.json, args {\"mode\":\"main\"}, CLI_END exit=0, stdout reply {...\"endpoint\":\"http://127.0.0.1:59546/mcp\",...\"pid\":28892,\"playing\":true}. The branch is cli_impl.rs:74-89 (GAME_START_TOOL) which publishes before printing."
    },
    {
      "id": "B2-ROUTE-FILE-REALLY-CHANGED",
      "pass": true,
      "evidence": "role_play_probe3.txt: ROUTE_BEFORE (10:27:43.270) = {endpoint :59429, pid 25424} with mtime 1790908040; ROUTE_FILE changed again 10:27:44.399 to {endpoint :59546, pid 28892}; ROUTE_AFTER mtime 1790908064. runs/smoke-t14/game_endpoint.json still holds exactly {endpoint http://127.0.0.1:59546/mcp, port 59546, source auto_free_port, pid 28892} and its mtime is 10:27:44. The new pid's process command line in the same transcript carries --scene res://scenes/main.tscn and \"--mcp-port=59546\". No fallback to the editor endpoint."
    },
    {
      "id": "B3-READINESS-WAIT-SHORT",
      "pass": true,
      "evidence": "CLI_START 10:27:43.271 (1790908063.272) to CLI_END 10:27:44.401 (1790908064.401) = 1.129 s; the route was rewritten at +1.127 s. tools.ready_timeout_seconds = 30 was never approached. The earlier successful invocation (role_play_probe2.txt, 10:27:18) took 1.617 s."
    },
    {
      "id": "B4-ROLE-CALLS-ARE-ZERO",
      "pass": true,
      "evidence": "My own census over the four unredacted trajectories: extra.actions[*].command with 'tools call editor_play_scene' = 0 in planner/developer.attempt1/developer.attempt2/tester; executed commands 16/211/89/123 = 439. So the branch was walked by the round author, never by a role."
    },
    {
      "id": "B5-PROBE-NOT-ROLE-BEHAVIOUR-IS-HONEST",
      "pass": true,
      "evidence": "The report's machine block states the verdict as 'EXERCISED BY A PROBE BY THE ROUND AUTHOR, NOT BY A ROLE' and section 3.4 opens with the same declaration. The prompts that make it structurally unreachable are unchanged (developer.md forbids editor_play_scene). Calling it a probe is the honest framing; the round does not claim role behaviour."
    },
    {
      "id": "B6-PROBE-INVENTORY-INCOMPLETE",
      "pass": false,
      "evidence": "Three invocations exist, not two: role_play_probe.txt (10:27:06, exit 5, -32602 scene_path), role_play_probe2.txt (10:27:18, exit 0, pid 25424 on :59429, elapsed 1.617 s), role_play_probe3.txt (10:27:43, exit 0, pid 28892 on :59546). Section 3.4 describes the failed one and the third one only, and labels the third 'the second'; role_play_probe2.txt appears in the evidence index but is never described, and its READINESS_DECOMPOSITION line prints 'route file first changed at +nans'. stop_scene.txt also labels the pid-25424 game 'probe 1'."
    },
    {
      "id": "C-E1",
      "pass": true,
      "evidence": "Directory emptiness is a self-authored capture (empty_proof.txt, 09:43:17: EXISTS_BEFORE False, mkdir, ENTRY_COUNT 0); init.txt exit 0 at 09:44:24; round_console.txt is a stream of exactly one run with --iterations 1. meta.start_state {mode:fresh, version_id:null}. My own re-implementation of policy.rs::hash_tree (relpath\\n{len}\\n{bytes}\\n, sorted, excludes .hoh/.git/.godot/.import) gives A0 3ac25f6c... 3 files/1727 B and A1 3d18b24d... 13 files/8254 B. versions/index.json has exactly two entries (iteration 0 role init, iteration 1 role developer, parent = A0). result.json evidence_diff = 10 added (5 scripts + 5 .uid) + scenes/main.tscn modified + 0 removed; attempts = planner RepeatedFormatError artifact_valid=true, developer 1+2 LimitsExceeded artifact_valid=true, tester RepeatedFormatError artifact_valid=true; iter-1 holds one plan.md with all three required sections."
    },
    {
      "id": "C-E2",
      "pass": true,
      "evidence": "The report scores E2 not_met and says so in the headline; that score is faithful to the product's own gate (exit 6, launchable=false). The criterion's two literal clauses are satisfied by the raw evidence: editor_play_scene answered playing=true (endpoint :63860, pid 7740), running_game_get_scene_tree returned 22 nodes after 1 poll, and pass 2 contains no Parse Error / Failed to load script. The report states this alternative reading explicitly and leaves it for the acceptance. I record the round's score as reproduced and the ambiguity as a risk, not as a report defect."
    },
    {
      "id": "C-E3",
      "pass": true,
      "evidence": "All four classes from game-endpoint semantic tools, recomputed by me from raw/input_replay.json and raw/interaction_evidence.json: move_right x 1817.99340820312 -> 2034.32434082031 delta +216.33093261719 (60 samples, 60 unique x); move_right_release +33.00073242188 (10/10); jump x constant 2096.65869140625 (unique 1), y 283.591979980469 -> min 234.258605957031 -> 267.480834960938 (unique 30); move_left 2085.65844726562 -> 1869.32629394531 delta -216.33215332031 (60/60). Four running_game_assert_node_state position:neq passed=true. interaction_evidence: running_game_get_node_properties /root/Main/HUD/Coins text 'Coins: 0' at call 0 -> 'Coins: 1' at call 48, plus assert text:neq actual 'Coins: 1' passed=true; Goal.reached false at calls 1/10/16/22/28/34/40 -> true at 46/49, assert reached:neq actual true passed=true. Battery observation text carries POSITION_ASSERT_PASSED 4, COIN_PICKED_UP 1, WIN_DRIVEN 1, and 0 of COIN_NOT_PICKED_UP/WIN_BLOCKED_UNDER_MOVE_RIGHT/WIN_UNREACHED_WITHIN_BUDGET/WIN_UNREACHABLE_GEOMETRICALLY/STALE_ACTION_NOT_RELEASED/COIN_COUNTER_UNREADABLE; coverage_shortfall_px=Some(-71.32836914062) with player max x 1671.32836914062 past goal x 1600.0. 0->1 is the first time in four rounds. The window's own seven position batches are 60/60 unique x each, and call[4] (move_left pressed:false, the stale release) precedes call[6] (move_right pressed:true, first driven batch)."
    },
    {
      "id": "C-E4",
      "pass": true,
      "evidence": "iter-1/evidence.json parses: qa_status partial, verified 11 [F1,F2,F3,F4,F5,F7,F10,F13,F16,N1,N2], gap 10 [F6,F8,F9,F11,F12,F14,F15,F17,N3,F5-COLL], overlap empty, no duplicate ids, 24 execution_records on verified + 17 on gap = 41, record types {assert:23, replay:10, runtime_trace:6, build:2}, every record candidate_id = 3d18b24d..., every path resolves inside iter-1/candidate (MISSING=[]), every gap carries player_impact and recommended_update, planner_handoff 3/4/5. result.json.prd_coverage repeats 11/10 with the same ids."
    },
    {
      "id": "C-E5",
      "pass": true,
      "evidence": "My own manifests: versions/3d18b24d..., iter-1/candidate and .workspace/fresh-t14 each hold the same 13 files / 8254 B with the same per-file sha256 (only_in=[], differing=[]), and all three trees hash to 3d18b24d... under my own implementation. QA did not modify A1."
    },
    {
      "id": "C-E6",
      "pass": true,
      "evidence": "iter-1/qa_report.md contains 'Status: **partial**.' and enumerates F6/F8/F9/F11/F12/F14/F15/F17/N3/F5-COLL as open, including 'N3 the editor error above' and 'no claim depending on them is verified'. No unmet item is reported as verified; the gap list matches evidence.json exactly. The report notes the token difference from T12/T13 ('Status: **partial**.' vs 'Verdict: partial')."
    },
    {
      "id": "C-GATE-REPRODUCTION",
      "pass": true,
      "evidence": "Artifact-level only (I cannot start an engine): gate_game_role_console.txt shows the empty-dir launch (PROJECT_PATH_ENTRIES [], PROJECT_GODOT_EXISTS False) resolving to '[MCP] role=game ... tools=73'; editor_launch_meta.txt shows the post-init launch on the same path resolving to role=editor, tools=154, same binary sha 08483088...e9e6a; scope_project_list_scripts.json replies {\"count\":0,\"scripts\":[]} while .workspace/mario/scripts has 15 entries; game_role_editor_status.json is -32601 Method not found; after_gate_kill_port.txt shows the gate pid 34448 gone with only TIME_WAIT. I parsed the two tools/list replies myself: game 73 = {project_:48, running_:23, os_:2} with 0 editor_*, editor 154 = {editor_:104, project_:48, os_:2} with 0 running_game_*; contract 177; served-but-not-in-contract 0; in-contract-not-served 104 all editor_. That is the fourth reproduction of the empty-dir role gate."
    },
    {
      "id": "C-ROLE-LIVE-ROUTE",
      "pass": true,
      "evidence": "My own census of the four unredacted trajectories: 33 commands contain running_game_* and they are all in tester.attempt1; paired returncodes are 32 x 0 and 1 x 1, and the single rc=1 command is a compound heredoc//tmp command that also contains running_game_ (so it is the command failing, not a refusal). 'game_endpoint_unavailable' appears in 0 tester tool replies, so 0 DR-43 refusals. planner/developer.attempt1/developer.attempt2 contain 0 running_game_* commands. Round-start, pass-1, repair-time and pass-2 game starts are documented as success/readiness-failure/readiness-failure/success, with warnings.log carrying the DR-70 line for :64294 and evidence/raw/live_snapshot_early.txt carrying :64097 pid 35444 at 09:45:19."
    },
    {
      "id": "C-E2-BEHAVIOURAL-NOTE",
      "pass": true,
      "evidence": "One asymmetry worth recording for the next batch: the '-e --path <dir>' engine resolves to role=game only when the directory has no project.godot; on the post-init directory the same binary is the editor. That is why the book's order (empty dir -> init -> point the editor -> run) is load-bearing, and why --fresh-workspace purging .godot/editor after the editor was already pointed at the project puts the cache directory under the editor's feet."
    },
    {
      "id": "G1-BASELINES",
      "pass": true,
      "evidence": "My own PowerShell digest (Get-ChildItem -Recurse -Force -File; repo-root-relative lowercase POSIX path + TAB + bytes + TAB + sha256; LF-joined with no trailing newline; culture-order Sort-Object; SHA-256 of the UTF-8 bytes) reproduces runs/smoke-t6 = 135 / c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03 / newest 2026-09-29 02:32:01 and all eleven rows exactly: t7 115/6e4c1595, t8 358/6d11b2c6, t9 83/541e2d81, t10 232/31955589, t11 186/a76c228f, t12 215/1d5889b7, t13 268/2d0ee05d, mario 178/dee0a36f, fresh-t11 100/4c07c0b6, fresh-t12 109/da56639b."
    },
    {
      "id": "G2-CALIBER-SENSITIVITY",
      "pass": true,
      "evidence": "Ordering and path prefix are load-bearing in my own scheme: an ordinal sort of .workspace/mario gives f622f5b04c39448443c38fdb34715ba47dd60c7917258649c2099d8b556c69be instead of dee0a36f..., and subtree-relative paths for runs/smoke-t9 give 0834b988de9b9a99acd3a11013c6573189f285443e936e9d6bdf5b59a3a0b21f instead of 541e2d81... . Both reproduce the T13 acceptance's published sensitivity findings."
    },
    {
      "id": "G3-FROZEN-AND-ENGINE",
      "pass": true,
      "evidence": "PRD-mario.md sha256 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a (unchanged); DECISIONS.md sha256 5621b2eaf8cbb36a81d4ed3d4257605c703bbfff0e137c698fcc7fd78e593e69 = the value the report publishes; REQUIREMENTS.md 298a9489...; engine binary 194216960 B sha256 08483088...e9e6a; nested engine godot-mcp/godot HEAD fc63af77c33368c4a1bb839c95d19750554f63a3 with empty git status --porcelain; git diff --name-status 8ddbad3..44131d9 touches no Cargo.toml/Cargo.lock. The four out-of-tree scratch files are the only untracked entries."
    },
    {
      "id": "G4-NO-WRITES-OUTSIDE-THE-ROUND",
      "pass": true,
      "evidence": "My own walk: 0 files under runs/** (excluding runs/smoke-t14) and 0 files under .workspace/mario, .workspace/fresh-t11, .workspace/fresh-t12 have mtime later than the round start 1790905513.791. The eleven baseline digests are unchanged at 11:00. Out-of-tree writes exist only as the four repository-root *.json files listed in result.json.out_of_tree_writes."
    },
    {
      "id": "G5-NOTHING-PUSHED-BEFORE-ACCEPTANCE",
      "pass": false,
      "evidence": "The report says 'HEAD == origin/master == 44131d9 (not pushed)'. That was true when written. It is no longer true: local origin/master is now 03ee2e3b4a2c1ef4536ec0108afec2741ce7581a (the round's own report-only commit, git show --stat = 1 file, TASK-SMOKE-T14-REPORT.md), and .git/logs/refs/remotes/origin/master records '44131d9... 03ee2e3... update by push' at epoch 1790909001 (10:43:21 +0800), while the local commit was made at 1790908630 (10:37:10) and this acceptance runs from 11:09. So the round artifact reached the remote before its independent acceptance (C5/D245 'push only after acceptance'). This is a dispatcher action after the report, not a false claim inside the report, but it is a process fact the next batch should know."
    },
    {
      "id": "G6-MACHINE-BLOCK",
      "pass": true,
      "evidence": "A line-anchored fence scan of TASK-SMOKE-T14-REPORT.md finds 60 fences and exactly one json block (lines 709-1303); it json.loads to 31 top-level keys and is byte-identical (26693 bytes, sha256 78b2d6c950a72062...) to runs/smoke-t14/evidence/analysis/machine_block.json, which is the file the report says build_json_block.py serialised with json.dump(..., ensure_ascii=False, indent=2) and assemble_report.py inserted byte-for-byte."
    },
    {
      "id": "G7-ROOT-SCRATCH-FILES",
      "pass": true,
      "evidence": "l.json 151 B, p2.json 153 B, pv.json 62 B, r.json 153 B, mtime 10:14-10:16, untracked, still present; content is the tester's scenario/args JSON, and pv.json is referenced in tester.attempt1.json. They are disclosed (sections 2.4, 5, 7.5, 10.6, machine block out_of_tree_writes) and kept as evidence; warnings.log has 0 lines containing out_of_tree_cleanup. is_root_temporary (src/runtime/hygiene.rs:162-174) accepts only .tmp_*/tmp_*/*.tmp/*.bak single components, so the batch's own bounded cleanup correctly cannot remove these four names - the report's explanation of why they survive is right."
    },
    {
      "id": "G8-FINAL-REVISION-GAP-VERDICT",
      "pass": true,
      "evidence": "I adjudicate the round's 'partially closed' answer as correct: HEAD 44131d9 has ec90c19 (DR-79) and 3e727b9 (DR-80) as ancestors (git merge-base --is-ancestor exit 0), the binary was rebuilt at 09:41:30 (12727808 B, sha 3b97e4a0...) and carries the DR-79 string constants (STALE_ACTION_NOT_RELEASED 1, route-publish readiness message 1, DSH_TERM_CMD 1), one complete round really ran on it, five of six criteria are met, but the round produced two reds that only hardware can expose (launch gate exit 6; redaction not effective). 'All green on real hardware' is not established, and the round says so."
    }
  ],
  "defects": [
    {
      "id": "T14A-1",
      "severity": "major",
      "what": "The report's second major (F-T14-2) states the mechanism is undetermined. It is determinable, and the defect is wider than the report states: the assignment scan loses whole variable families whenever one trajectory repeats the environment dump. In developer.attempt1.redacted.json the raw survivors are not only DSH_TERM_CMD (4) but also HOH_GAME_ROUTE (4), HOH_ROLE (4), HOH_RUN_DIR (4), HOH_RUN_ID (4), HOH_SCRATCH_DIR (4), HOH_TOOLS_ENDPOINT (4), HOH_VIEW_DIR (4), HOH_ITERATION (4), HOH_HOH_BIN (4) and HOH_ARTIFACT_DIR (4); developer.attempt2.redacted.json still leaves DSH_TERM_CMD (2) and HOH_GAME_ROUTE (4). The pre-existing HARNESS_ENV_VARS class is therefore not reliably redacted either, so DR-79 (4) has not closed the disclosure class it claims to close.",
      "reproduction": "Port src/runtime/secrets.rs:311-469 (splice_assignments, assignment_value_end, is_value_terminator, command_line_value_ends_at, looks_like_json) to bytes and run it over runs/smoke-t14/iter-1/traj/developer.attempt{1,2}.json: the output is byte-identical to the two *.redacted.json sidecars. Span sets: attempt1 {HOH_MODEL_API_KEY:4, OPENAI_API_KEY:1, PATH:2}; attempt2 {HOH_MODEL_API_KEY:4, HOH_ROLE:1, HOH_RUN_DIR:1, HOH_RUN_ID:1, HOH_SCRATCH_DIR:1, HOH_TOOLS_ENDPOINT:1, HOH_VIEW_DIR:1}. Instrumenting the guard at secrets.rs:324 shows every HOH_* and DSH_TERM_CMD candidate reported as SKIP(overlap) with the blocking end being OPENAI_API_KEY's span at 286080-286095. Minimal plant: the text 'DSH_TERM_CMD=cd /f/moonbit-hof-rs && python run.py --out x.txt\\ntail\\nfiller\\nOPENAI_API_KEY=\\nmore\\n' leaves DSH_TERM_CMD raw; deleting the single later 'OPENAI_API_KEY=' line makes the identical DSH_TERM_CMD line redact. The two unit tests at src/runtime/secrets.rs:1348-1376 and :1384-1416 use one-assignment fixtures with no repeated dump, so they pass by construction and cannot catch this."
    },
    {
      "id": "T14A-2",
      "severity": "minor",
      "what": "Section 2.1 describes the developer's scene as 'Ground/Player/Coin1/Coin2/Goal/Enemy1/HUD/Wall ... 22 nodes'. The frozen candidate has no Coin2 and no Wall.",
      "reproduction": "Read runs/smoke-t14/iter-1/candidate/scenes/main.tscn (3500 B): the [node ...] lines are Main, Ground(+2), Player(+3 incl. Camera2D), Coin1(+2), Goal(+2), Enemy1(+2), HUD(+4) = 22 nodes; 'Coin2' and 'Wall' do not occur. The same tree is in raw/scene_tree.json and candidate/raw/play_scene_ready.json. (The 22 count and the '~1 coin' reading in section 2.3 are correct.)"
    },
    {
      "id": "T14A-3",
      "severity": "minor",
      "what": "Caliber A's tools_call column is not reproducible. The report publishes planner 0, developer.attempt1 10, developer.attempt2 37, tester 64, total 111. Counting occurrences of the substring 'tools call' in extra.actions[*].command gives 0/11/37/64 = 112; counting command lines gives 0/11/32/33 = 76.",
      "reproduction": "python: for each unredacted trajectory, sum cmd.count('tools call') over extra.actions[*].command. developer.attempt1's eleventh is the literal command '\"target/release/hoh.exe\" tools call --help', which is plausibly what the author excluded to get 10 - but the report does not state that exclusion, and its stated caliber ('counted per command line') matches neither reading."
    },
    {
      "id": "T14A-4",
      "severity": "minor",
      "what": "The probe inventory is incomplete. Section 3.4 says there were two probe invocations (one failed on arguments, one succeeded) and that 'both probes started one game each'. There were three invocations, and the middle one - role_play_probe2.txt - is the one that first proved the route republish from a clean (absent) route.",
      "reproduction": "evidence/probe/role_play_probe2.txt: T0 10:27:18.391, ROUTE_BEFORE exists=False, CLI_START 10:27:18.392, NEW_GODOT_PROCESS pid 25424 with \"--mcp-port=59429\", CLI_END 10:27:20.009 elapsed=1.617 exit=0, ROUTE_AFTER {endpoint :59429, pid 25424} mtime 1790908040. Its own READINESS_DECOMPOSITION line prints 'route file first changed at +nans'. stop_scene.txt labels the pid-25424 game 'probe 1' while the file numbering makes it the second. The report cites only role_play_probe.txt and role_play_probe3.txt in prose; role_play_probe2.txt appears only in the appendix index."
    },
    {
      "id": "T14A-5",
      "severity": "info",
      "what": "start_round_game_attempts[0] is recorded as outcome 'success' on the strength of the route file existing at 09:45:19 (read at 09:46:19) - there is no reply transcript for :64097, unlike T13 where the author POSTed to :53068 itself. The inference is sound (the runtime publishes a role/round-started route only after readiness) but it is an inference from the route file, not a measured reply.",
      "reproduction": "evidence/raw/live_snapshot_early.txt contains only the route-file content/mtime and meta fields; no HTTP call to :64097 appears in it. The same file does show meta.engine.mcp.game_endpoint = null, i.e. it was read before the runtime recorded its own game endpoint."
    },
    {
      "id": "T14A-6",
      "severity": "info",
      "what": "The frozen sidecar also names config/model.secret.env through a second route the report does not mention: the Developer's own directory listing of config/.",
      "reproduction": "python: 'model.secret.env' occurs 2x in developer.attempt1.json and 2x in developer.attempt1.redacted.json (and 0x in attempt2). The context is a tool reply '<returncode>0</returncode>\\n<output>\\nhoh.yaml\\nmodel.secret.env\\n</output>' to a `cd config && ls`-style command. The 51-byte value still does not appear anywhere (0 hits)."
    }
  ],
  "risks": [
    "The launch gate closes on any non-banner, non-stale editor-log line, so a clean project can be frozen launchable=false and exit 6 (what happened here). The same predicate is the only detector of real script errors (the pass-1 res://scripts/main.gd:8 Parse Error), so the fix must be an additive exemption, not a relaxation.",
    "--fresh-workspace purges .godot/editor/** after the book's mandated order has already pointed the editor at the project; whether the editor recreates the directory is not deterministic across rounds, so the same exit 6 can recur on any round.",
    "The assignment scan at src/runtime/secrets.rs:311-363 drops variable families whenever one artifact repeats a dump; today only paths and a command line leak, but the same losing race would apply to any assignment that appears in a repeated dump, including a credential if one ever reached the shell environment.",
    "editor_get_errors is an editor-log-tail reading (in-round filesystem_cache10 vs later [MCP] capture=off), yet the gate treats it as a hard verdict on the project.",
    "The 64 KiB output cap fired again on a real 79928-byte payload (tester.attempt1 message 29), so any analysis that trusts a role's in-context view silently loses the tail.",
    "The round's report-only commit is already on origin/master before this acceptance (reflog 10:43:21), so the C5 'push only after acceptance' invariant was not held by the dispatch side even though the report itself claimed nothing had been pushed.",
    "Untracked scratch files keep the repository dirty and are outside every baseline; the bounded cleanup correctly refuses names it was never specified to remove, so this class will recur unless the writer (not the cleaner) is fixed.",
    "Empty-directory proofs and engine consoles remain self-authored captures in every round; the only independent corroboration is the deterministic A0 identity and start_state=fresh, which cannot rule out a pre-populated directory that was later emptied."
  ],
  "unverified": [
    "The empty-directory proof (evidence/round/empty_proof.txt) and every engine console/launch capture are self-authored and cannot be re-derived offline; I verified their internal consistency and cross-checked the raw MCP replies they contain, nothing more.",
    "I did not start the engine, run a round, or touch the network, so the role-gate reproduction (73 vs 154 tools) is verified as artifacts plus my own parse of the two tools/list replies, not by a fresh launch.",
    "I did not verify the stale predecessor binary sha256 310075fa...7158ca; freshness rests on mtime 1790905290, the DR-79 string constants in the binary, and the fact that my port of the current source reproduces the current artifacts' redaction exactly.",
    "I did not trace the QA report's own narrative numbers (e.g. 'min y 210.36, back to 303.97'), which occur 8 and 6 times in tester.attempt1.json and therefore come from the Tester's own live probing, but I did not map them to a specific reply.",
    "I did not pixel-analyse the 11 PNGs, and I did not audit the author's analysis scripts line by line; I re-derived every load-bearing number from the frozen payloads instead.",
    "I did not verify the wall-clock timing instrumentation in the staging scripts (run_stream.py), so elapsed times are taken from the transcripts plus the round console.",
    "I did not examine the behaviour of the redactor at lengths below/above the samples I ported (only the ASCII-dominant real files and synthetic plants)."
  ],
  "task": "TASK-SMOKE-T14-ACCEPTANCE",
  "kind": "independent acceptance of the final-revision real round (no upstream context, no round executed, offline)",
  "round_id": "smoke-t14",
  "reviewed_report": ".spec/hof-rs/tasks/TASK-SMOKE-T14-REPORT.md",
  "reviewed_against_head": "03ee2e3b4a2c1ef4536ec0108afec2741ce7581a",
  "round_head_reported": "44131d983ed100a65775d5dfa865bcc6ed7fa4a4",
  "verdict_scope": "The headline claims are independently reproduced: exit code 6 with one gate reason that names only the editor cache-write line; the gate cannot separate that from a project defect; the four counterexamples hold; the redaction gap is real and I determined its mechanism (a span-ownership aliasing bug, reproduced byte-for-byte); the probe really walked the republish branch and changed the route; E1/E3/E4/E5/E6 and the role census reproduce from raw payloads; the eleven baselines reproduce under my own digest; the machine block parses and is byte-identical. What fails is one minor report defect (B6/T14A-4: a third probe invocation is undescribed) plus three count/description inaccuracies (T14A-2, T14A-3) and one process fact (G5: the round commit reached origin/master before acceptance). No load-bearing claim of the report is false.",
  "honest_disclosure": [
    "I wrote nothing under runs/**; all temporary material lives in C:\\Users\\wyl\\AppData\\Local\\Temp\\t14acc.",
    "I did not modify the reviewed report, the frozen specification, DECISIONS.md, godot-mcp/**, the workspaces or the four repository-root scratch files.",
    "I did not stage, commit or push anything; this acceptance file is the only file I created inside the repository.",
    "I performed no rm -rf and constructed no path from an unexpanded variable."
  ]
}
```

## 0. 机器可读判定（由 `json.dumps(..., ensure_ascii=False, indent=2)` 生成，落盘后按行锚定栅栏 `json.loads` 回读；本块即文件开头，位于标题之前）


# TASK-SMOKE-T14-ACCEPTANCE — 独立验收：**最终修订版真机轮**（退出码 6 的缺口红、真机脱敏缺口、角色自起场景探针、E1..E6、守卫）

- 验收者：**全新独立验收子代理**（无上游对话上下文；不继承实施者或调度者结论）
- 被验收对象：`.spec/hof-rs/tasks/TASK-SMOKE-T14-REPORT.md`（**只用于定位**，不作证据）
- 复核口径：`REQUIREMENTS.md` E1..E6、`.spec/hof-rs/OBJECTIVE-COMPLETION.md`、`TASK-SMOKE-T12.md`、`TASK-SMOKE-T13.md`、`TASK-SMOKE-T13-ACCEPTANCE.md`、`DECISIONS.md` D289–D293
- 时间：2026-10-02 11:09 (+0800)；**全程离线**：未启动引擎、未跑任何轮次、未联网
- 我自己产生的原始读数：`runs/smoke-t14/**`、`.workspace/fresh-t14/**`、`.workspace/mario|fresh-t11|fresh-t12/**`、`runs/smoke-t6..t13/**`、`src/**`（只读）、`git` 只读命令

## 1. 逐项核对表（机器块的 `criteria` 是同一批读数的结构化形式；此表为可读版）

| # | 检查项 | 我的独立读数 | 判定 |
|---|---|---|---|
| `H1` | 退出码四处同数 | `36 0A` / `36 0A` / meta 6 / ROUND_EXIT 6 | **成立（=6）** |
| `H2` | 门裁决与其 reason | 唯一 reason 指向 `editor_errors_baseline` 的 `res://.godot/editor/filesystem_cache10` 写失败；`launchable=false` | **成立** |
| `H3` | 门能否区分基建与项目缺陷 | `evaluate_launchable` 要求每个 gate 步 ok；编辑器步只豁免 DR-48 的 `[MCP]` 横幅与 DR-68 的 `res://file:line`＋`"X()"` 陈旧行 ⇒ 缓存写失败被判为项目缺陷；另一半门是绿的 | **成立（确实不能区分）** |
| `H4` | 不是权限 | `icacls` 对 fresh-t14\\.godot 与 fresh-t13\\.godot 逐行相同 | **成立** |
| `H5` | 不是普遍行为 | `filesystem_cache10` 在 mario/11/12/13 存在（1241/673/805/789 B），fresh-t14 整个 `.godot/editor/` 不存在 | **成立** |
| `H6` | pass 1 有真脚本错误、修复真的修好 | pass1 raw `count=6` 含 `res://scripts/main.gd:8 - Parse Error`；pass2 raw `count=1` 只剩缓存行；`repair_retry_used=true` | **成立** |
| `H7` | 该字段不稳定 | 轮后同一 pid 36808 返回 `[MCP] capture=off …`（非错误行） | **成立** |
| `H8` | 修门不得丢掉脚本错误检测 | `editor_error_is_stale` 对无 `"X()"` 的解析错误行返回 false（保留）⇒ 真脚本错误正是被这条粗谓词抓住的 ⇒ 修法必须是**追加式豁免** | **成立（判据）** |
| `R1` | `DSH_TERM_CMD` 逐字存活 | attempt1 副本 4 处 raw / 0 处 marker；attempt2 副本 2/0 | **成立** |
| `R2` | `HOH_GAME_ROUTE` 逐字存活 | 两份副本各 4 处 raw；`<redacted>` 0 处 | **成立** |
| `R3` | 同一转储里别的名字被脱敏 | attempt1：`HOH_MODEL_API_KEY` 4、`PATH` 2、`PSMODULEPATH` 1；attempt2：另加 6 个 `HOH_*` 各 1；marker 总 7 / 10 | **成立** |
| `R4` | 密钥值不出现 | 51 B 密钥对 391 个文件 **0 命中** | **成立** |
| `R5` | 机理未定 vs 我定出机理 | 忠实移植 `secrets.rs:311-469` ⇒ 两份旁路副本**逐字节复现**；根因 = `secrets.rs:324` 的 `start < span.end` 全局前向守卫 | **报告保守不假，机理已定** |
| `R6` | 单测是否可能充分 | 两个 DR-79④ 单测都是**单赋值夹具**；我的最小植入证明：同一行 `DSH_TERM_CMD=` 因后面多一条 `OPENAI_API_KEY=` 而不被脱敏 | **成立（单测构造上不充分）** |
| `B1` | 探针真的发了 `editor_play_scene` | `--role developer`、exit 0、回包 `playing=true pid=28892 :59546` | **成立** |
| `B2` | 路由文件真的从陈旧换成新的 | `:59429/25424` → `:59546/28892`（10:27:44.399），与 `game_endpoint.json` 现值一致 | **成立** |
| `B3` | 就绪等待很短 | 整条 1.129 s，路由改写 +1.127 s；30 s 超时未靠近 | **成立** |
| `B4` | 角色侧从未调用过该工具 | 四条未脱敏轨迹 `editor_play_scene` = 0；executed 439 | **成立** |
| `B5` | 「探针≠角色行为」的定性诚实 | 报告与机器块都写明 EXERCISED BY A PROBE, NOT BY A ROLE | **成立** |
| `B6` | 探针清点 | 实际**三次**调用；`role_play_probe2.txt`（pid 25424/:59429）未被描述，且其分解行印 `+nans` | **不成立（minor）** |
| `C-E1` | E1 | A0 `3ac25f6c…` 3/1727 → A1 `3d18b24d…` 13/8254（我自算）；`start_state=fresh`；`versions/index.json` 仅 2 条；三节 plan.md 齐备；4 条 attempt | **成立（met）** |
| `C-E2` | E2 | 产品自己的门 `launchable=false` ⇒ 报告的 not_met 忠实；但判据字面两半（可启动、无脚本错误）由原始件满足 | **报告得分成立；歧义记入风险** |
| `C-E3` | E3 | 四类全齐，数值逐条复算命中；`Coins: 0 → 1` 与 `Goal.reached false → true` 均来自游戏端点回包并带引擎断言 `passed=true` | **成立（met，且首次 0→1）** |
| `C-E4` | E4 | 11 verified / 10 gap、overlap 空、41 条记录（24/17）、`MISSING=[]`、candidate 单一、handoff 3/4/5 | **成立（met）** |
| `C-E5` | E5 | 三棵树同 13 文件/8254 B、逐文件 sha 相同、我自算 hash 同一 | **成立（met）** |
| `C-E6` | E6 | `qa_report.md` 逐字 `Status: **partial**.` 并逐条列 gap；未达成未写成 verified | **成立（met）** |
| `C-GATE` | 启动角色门复现 | 空目录 role=game/73（`{project_:48, running_:23, os_:2}`、0 editor_*）、init 后 role=editor/154（0 running_game_*）、契约 177、`editor_status` -32601；同二进制 | **成立（第 4 次复现，但为工件级）** |
| `C-ROLE` | 角色侧 live 路由 | 33 条命令：32 rc=0、1 rc=1（该命令自身失败）、0 条 DR-43；回包文本 0 次 `game_endpoint_unavailable` | **成立** |
| `G1` | 11 条只读基线 | 我自写 culture-order 口径先命中锚点 `runs/smoke-t6 = 135 / c144ef32…7a9c03`，11/11 与报告表逐字一致 | **成立** |
| `G2` | 口径敏感性 | 序数排序 mario `f622f5b0…`；子树相对路径 t9 `0834b988…` ⇒ 排序与前缀都承重 | **成立** |
| `G3` | 冻结件/引擎/Cargo | PRD `4c81c3a9…`；DECISIONS `5621b2ea…`（= 报告值）；REQUIREMENTS `298a9489…`；引擎 `08483088…`；嵌套仓 HEAD `fc63af77…` porcelain 空；Cargo 未被 8ddbad3..44131d9 触及 | **成立** |
| `G4` | 轮外无写 | 轮开始后 `runs/**`（除 smoke-t14）0 个文件、三个只读工作区 0 个文件 | **成立** |
| `G5` | 收工前未 push | 报告称未 push（当时为真）；但 `origin/master` 现已是本轮报告提交 `03ee2e3`（reflog: update by push @10:43:21，早于本次验收） | **不成立（流程项）** |
| `G6` | 机器可读块 | 行锚定 60 栅栏、1 个 json 块、31 键、`json.loads` 通过、与 `machine_block.json` 逐字节同（26693 B / `78b2d6c9…`） | **成立** |
| `G7` | 仓根 4 个 scratch | 实测 151/153/62/153 B，10:14–10:16，未跟踪；已在报告披露；`is_root_temporary` 不含这些名字 ⇒ 批次自己的清理逻辑解释得通 | **成立** |
| `G8` | 「最终修订缺口」结论 | 支持与反对两侧我逐条复核；「部分闭合」是准确表述 | **成立** |

**总判定：`pass`**（范围见 JSON 的 `verdict_scope`）。头条、探针、E1..E6、角色普查、守卫、机器块都被我独立复算；报告没有承重性的假陈述。失败项是一处 minor 报告缺陷（第三次探针未描述）、两类计数/描述不准、以及一条供货方流程事实（报告提交先于验收到了远端）。

## 2. 我自己做的植入与反例

1. **脱敏器的逐字节重实现（最强植入）**：把 `splice_assignments`/`assignment_value_end`/`is_value_terminator`/`command_line_value_ends_at`/`looks_like_json` 按字节移植到 Python，喂入两份原件，**输出与两份 `*.redacted.json` 逐字节相同**（spans 7 与 10，名字集合逐个吻合）。这不是「解释」，是**可复制的因果**。
2. **守卫别名化的最小种植**：文本 `DSH_TERM_CMD=cd …\ntail\nfiller\nOPENAI_API_KEY=\nmore\n` ⇒ `DSH_TERM_CMD` 原样存活；**只删掉后面那一行** `OPENAI_API_KEY=` ⇒ 同一行 `DSH_TERM_CMD` 被脱敏。证明失败与内容无关，只与「后面出现过更晚的、更早被扫描的名字」有关。
3. **单测夹具反例**：我的移植对 `secrets.rs:1348` 与 `:1384` 两个夹具都正确脱敏 ⇒ 单测通过是**构造性**的，与真机形态无关（真机形态是同一条转储在轨迹里重复出现）。
4. **摘要口径自证与敏感性**：自写 PowerShell 口径复现任务书锚点 `runs/smoke-t6`；序数排序与子树相对路径各改一次值 ⇒ 口径承重。
5. **树 hash 重实现**：`relpath\n{len}\n{bytes}\n` 独立实现复算 A0/A1 与三棵树同一。
6. **端点归属反例**：我亲自解析两份 `tools/list` 原始回包 ⇒ 游戏端点 23 个 `running_*`、0 个 `editor_*`；编辑器端点 0 个 `running_game_*` ⇒ E3 的回包不可能来自编辑器。
7. **截断反例**：解析 `extra.hoh_output_truncated`（而非 grep 字节）⇒ tester 第 29 条消息 1 次（65536/79928）。
8. **计数口径反例**：`tools call` 的「出现次数」与「命令条数」两种读法都得不出报告的 10/37/64/111（实为 112 或 76）。
9. **权限反例**：`icacls` 逐行比较 fresh-t14 与 fresh-t13 的 `.godot`。
10. **时间窗反例**：以 `1790905513.791` 为界 Python 递归遍历 `runs/**` 与三个只读工作区（不用 WSL bash）。

## 3. 独立判断（逐条回答本批的五个任务）

**3.1 头条（门红）**：退出码 6 与门的裁决/唯一 reason 都成立，reason 指向的确实是编辑器缓存写失败（`res://.godot/editor/filesystem_cache10`），而不是产出的工程——工程侧 `scenes/main.tscn`、5 个脚本、22 节点、`play_scene`/`game_endpoint` 全绿。四条反例我全部复核成立（权限逐行相同、四个别工程都有该文件、pass 1 真有 `main.gd:8` 解析错误且被修复重试修掉、轮后同一进程的该字段返回另一条非错误行）。**门确实不能区分「基建/缓存故障」与「项目缺陷」**：它的两个必选步给出相反信号，而缓存路径本来就被运行时排除在 hash/快照之外。**任何修法都必须保住真脚本错误检测**——目前这条粗谓词（非 `[MCP]` 横幅、非 DR-68 陈旧行即失败）正是唯一抓住 pass 1 解析错误的东西，`editor_error_is_stale` 对解析错误行返回 false（fail-closed），所以正确方向是**追加式豁免缓存路径**，而不是放宽谓词。

**3.2 脱敏缺口**：成立且比报告更宽。我在两份旁路副本里复算：`DSH_TERM_CMD` raw 4/2、`<redacted>` 0；`HOH_GAME_ROUTE` raw 4/4、`<redacted>` 0；同一份转储里 `HOH_MODEL_API_KEY`（4）与 attempt2 的另外 6 个 `HOH_*` 被脱敏；marker 总数 7/10；51 B 密钥值 0 命中。**「机理未定」是诚实但保守的：机理现已确定**（`secrets.rs:324` 的全局前向 `start < span.end` 守卫 + 同一转储在轨迹里重复出现），且**单测在构造上不可能充分**——两个夹具都只有单个赋值、没有重复转储，而真机轨迹把整条环境转储重复了 4 次。附带发现：报告未提到的 `config/model.secret.env` 二次披露路径（Developer 自己 `ls config` 的输出，2 处）也在冻结件里。

**3.3 悬挂三轮的分支**：探针**真的**发了 `editor_play_scene`（role=developer，exit 0），**真的**成功，**真的**把路由文件从陈旧的 `:59429/pid 25424` 换成新游戏的 `:59546/pid 28892`，整条命令 1.129 s（就绪等待 ≈1.1 s，远低于 30 s 上限）。它**部分闭合**了这个问题：代码路径（`cli_impl.rs:74-89`）被证明可用，且角色侧 live 路由本轮再次规模性地可用（33 条、0 拒绝）；但角色自己**仍然 0 次**调用该工具（提示词结构性禁止），所以「角色自起场景」仍是**未成为行为**的分支。把它称作「探针」而非「角色行为」是诚实的；不诚实的是清点：共**三次**调用，中间那次（`role_play_probe2.txt`）才是第一次证明「从无路由到新路由」的成功，报告只描述了第一与第三次。

**3.4 其余判据与启动门**：E1/E3/E4/E5/E6 全部由我自己的脚本从原始件复算成立，尤其 E3 的四类读数逐位命中、金币首次 `0→1`、胜负 `false→true` 均带引擎侧 `passed=true`，且我验证了这些回包只能来自游戏端点。启动角色门第 4 次复现（空目录 73/role=game、init 后 154/role=editor，我亲自解析两份 `tools/list`），角色侧 live 调用 33 条 / 32 成功 / 0 拒绝也成立。E2 的报告得分我接受为**产品口径下的忠实记分**，同时如实记录：判据字面两半由原始件满足——这是本批最有价值的歧义，应由决策层裁定「E2 以判据字面读还是以产品的门读」。

**3.5 守卫与诚实**：11 条只读基线在我自写口径下逐字节未变（含 t6 锚点），且序数排序/路径前缀会让值不同（口径确实承重）；冻结规范、`DECISIONS.md`、引擎树、Cargo 未动；轮外无写入；机器块由序列化器生成、单块、可解析、与 `machine_block.json` 逐字节同；仓根 4 个 scratch 被披露且被批次自己的清理谓词正确地排除在外（`is_root_temporary` 只收 `.tmp_*`/`tmp_*`/`*.tmp`/`*.bak`）。**唯一不成立的是「未 push」所隐含的状态**：本轮的报告提交 `03ee2e3` 现已在 `origin/master` 上（reflog `update by push` @10:43:21），早于本次独立验收。报告的机器块语义我在整体上判为诚实：`not_met`、`launchable=false`、`repair_retry_used`、pass 1 失败、两条 major、四条未定因、以及「仅部分闭合」都写在明面上。

## 4. 缺陷清单（结构化见 JSON 的 `defects`）

| id | 级别 | 一句话 |
|---|---|---|
| `T14A-1` | major | 「脱敏机理未定」可以定，且缺陷比报告写的宽：`secrets.rs:324` 的守卫使 `HOH_*`/`DSH_TERM_CMD` 整族在重复转储下存活；我已逐字节复现并给出最小植入 |
| `T14A-2` | minor | §2.1 的场景节点清单含不存在的 `Coin2`/`Wall`（22 个节点数正确） |
| `T14A-3` | minor | 口径 A 的 `tools_call` 列不可复算（出现次数 11/37/64=112；命令条数 76；报告 10/37/64=111） |
| `T14A-4` | minor | 探针实际三次，`role_play_probe2.txt` 未被描述且其分解行印 `+nans` |
| `T14A-5` | info | `:64097` 的「成功」是从路由文件存在性推断的，没有回包转录 |
| `T14A-6` | info | 冻结件另经 Developer 自己的 `ls config` 披露了 `config/model.secret.env`（2 处），报告未提 |

## 5. 未证实项（附理由）

1. The empty-directory proof (evidence/round/empty_proof.txt) and every engine console/launch capture are self-authored and cannot be re-derived offline; I verified their internal consistency and cross-checked the raw MCP replies they contain, nothing more.
2. I did not start the engine, run a round, or touch the network, so the role-gate reproduction (73 vs 154 tools) is verified as artifacts plus my own parse of the two tools/list replies, not by a fresh launch.
3. I did not verify the stale predecessor binary sha256 310075fa...7158ca; freshness rests on mtime 1790905290, the DR-79 string constants in the binary, and the fact that my port of the current source reproduces the current artifacts' redaction exactly.
4. I did not trace the QA report's own narrative numbers (e.g. 'min y 210.36, back to 303.97'), which occur 8 and 6 times in tester.attempt1.json and therefore come from the Tester's own live probing, but I did not map them to a specific reply.
5. I did not pixel-analyse the 11 PNGs, and I did not audit the author's analysis scripts line by line; I re-derived every load-bearing number from the frozen payloads instead.
6. I did not verify the wall-clock timing instrumentation in the staging scripts (run_stream.py), so elapsed times are taken from the transcripts plus the round console.
7. I did not examine the behaviour of the redactor at lengths below/above the samples I ported (only the ASCII-dominant real files and synthetic plants).

## 6. 我没有检查的

- 未启动引擎、未跑轮、未联网；`runs/**` 我一字节未写（临时材料全在 `C:\Users\wyl\AppData\Local\Temp\t14acc`）。
- 未逐行审读作者的分析脚本（`evidence/scripts/**`）；我改为从冻结载荷自行复算每一个承重数字。
- 未看 11 张 PNG 的像素；未验证 `qa_report` 里 Tester 自采数字对应的具体回包。
- 未修改被验收报告、冻结规范、`DECISIONS.md`、`godot-mcp/**`、任何工作区；未删除仓根 4 个 scratch；未 stage/commit/push。
- 未使用 `rm -rf`，未从未展开的变量构造路径。
- 顺带观察（与轮次无关）：仓根有一个**被跟踪**的 `%DST%` 目录（10-01 16:03），不在任何基线内，属上一批的遗留物；我未触碰。

## 7. 给下一批的建议

1. **先修门，且必须追加式**：为 `editor_errors_baseline` 加一条**具名豁免**（例如 `res://.godot/editor/**` 或引擎缓存写失败文案），保留「非横幅、非陈旧 ⇒ 失败」的默认；并补测试：真解析错误仍必须关门、缓存写失败不得关门（双向钉）。
2. **修脱敏的守卫，而不是它引用的行**：把 `splice_assignments` 的 `start < span.end` 改成**真正的区间重叠测试**（或按名字分别维护游标），并加「同一条转储在文件里重复 2..4 次」的夹具（名字顺序与文件中出现顺序不一致、且某个名字的最后一次出现在文件尾部）；否则 DR-79④ 与既有的 `HARNESS_ENV_VARS` 一起继续漏。
3. **把「本轮报告提交不得先于验收推送」机械化**：本轮 `03ee2e3` 已在远端（reflog 10:43:21），与 C5/D245 冲突；建议让推送闸门显式拒绝「最新提交是 round report 而验收文件还不存在」的状态。
4. **E2 的口径需要决策层裁定**：请明确「E2 以判据字面（可启动、无编译/脚本错误）读，还是以产品 `artifact_gate.launchable` 读」；本轮两种读法给出相反记分，而报告已诚实披露。
5. **`--fresh-workspace` 与编辑器顺序**：把「清空工作区会删掉编辑器已指向工程的 `.godot/editor/`」写进任务书的已知副作用，并要求轮次记录 `.godot/editor/` 的存在性时间线（本轮只留了事后形状，未插桩落盘时刻）。
6. **报告纪律的两条机械检查**（承接 T13A-2 的教训并扩展到本轮）：任何计数列都要写明「数的是出现次数还是命令条数」并由脚本产出；任何探针/启动清点都要由脚本枚举**所有**同类工件（本轮 `probe2` 就是这样漏掉的）。
7. **`editor_get_errors` 语义**：它读的是编辑器日志尾，不是稳定的项目诊断；建议在门的证据里同时给出「该行是否属于被排除的缓存路径」，让下一批不必重复本轮的四条反例劳动。
