```json
{
  "task": "TASK-SMOKE-T13-ACCEPTANCE",
  "kind": "independent acceptance of the T13 reproducibility round (no upstream context, no round executed, offline)",
  "round_id": "smoke-t13",
  "reviewed_report": ".spec/hof-rs/tasks/TASK-SMOKE-T13-REPORT.md",
  "reviewed_against_head": "4c8e76a88f3ec0612d9b50300d6521dab8402fa7",
  "round_head_reported": "8ddbad3f4db43c28be158c17ad0678fe4d77857c",
  "verdict": "fail",
  "verdict_scope": "All six criteria E1..E6 and the round's headline answer (outcome class reproducible, bytes not) are independently reproduced from raw payloads, and the guards hold. What fails is the report's own report-discipline and mechanism claims: (1) the central causal story of the round - 'the round's game start failed readiness at 04:17:44 and no route existed for any role until battery pass 2' - is contradicted by the round's own evidence (a live published game endpoint at http://127.0.0.1:53068/mcp was probed by the round author at 04:19:22, and warnings.log was last written at 04:41, not 04:17:44); (2) the report states the 64 KiB truncation path was never triggered, but the Tester's trajectory contains a real truncation (81139 B -> 65536 B) at 04:56:37; (3) the artifact_valid looseness is attributed to the wrong code path. No re-run of the round is needed; the report and its mechanism section need correction, and the newly observed facts should feed the next batch.",
  "criteria": [
    {
      "id": "E1",
      "pass": true,
      "evidence": "Independently reproduced: A0 tree id 3ac25f6c5c38885febd3a001ea99c88aca61b1799c7b105306919886c2c1d151 = 3 files/1727 B with my own re-implementation of policy.rs::hash_tree (relpath\\n{len}\\n{bytes}\\n, sorted, .hoh/.git/.godot/.import/node_modules/target excluded); A0 project.godot sha256 00d02c9c...c0ef4 identical to smoke-t11 and smoke-t12 A0; A1 = a54179ce... 13 files/9610 B, 10 added / scenes/main.tscn 342->4335 B / 0 removed; start_state {mode:fresh}; result.json ok=true, attempts planner RepeatedFormatError artifact_valid=true, developer 1+2 LimitsExceeded artifact_valid=true, tester Submitted; exit_code bytes 30 0A, process_exit_code bytes 30 0A, meta.exit_code 0, wrapper EXIT_CODE 0; artifact_gate {applicable:true,launchable:true,reasons:[]}. Empty-directory listing is a self-authored capture (cannot be re-derived); the deterministic A0 scaffold corroborates it."
    },
    {
      "id": "E2",
      "pass": true,
      "evidence": "From raw payloads: editor_errors_baseline {count:0,errors:[],pid:948,port:9877}; play_scene_ready editor_play_scene playing=true pid=30728 endpoint http://127.0.0.1:51223/mcp then running_game_get_scene_tree ok with 28 nodes (I counted the tree myself); screenshot frame-00.png present (6240 B); editor_stop_scene stopped=true; artifact_gate launchable=true in meta.json and result.json; battery 12/12 steps ok=true in pass 2."
    },
    {
      "id": "E3",
      "pass": true,
      "evidence": "From raw payloads of pass 2: input_replay move_right x 1773.99353027344->1795.07604980469 delta +21.082520 with 26/60 unique x; move_right_release delta +0.916626 2/10 unique; jump x constant 1794.10217285156 (unique 1) and y 279.979614257812 -> min 224.257385253906 -> 252.590744018555 (unique 30); input_replay move_left x 1786.76892089844->1570.43798828125 delta -216.330933 60/60 unique; battery.json carries exactly four 'POSITION_ASSERT_PASSED' lines (jump, move_left, move_right, move_right_release); interaction_evidence raw replies running_game_get_node_properties give Coins: 0 (call 0) -> Coins: 2 (call 48) and Goal.reached false (calls 1/10/16/22/28/34/40) -> true (calls 46/49); running_game_assert_node_state text:neq 'Coins: 0' actual 'Coins: 2' passed=true and reached:neq false actual true passed=true. Tool-set census I ran: game role serves 73 tools with 23 running_game_* and 0 editor_*; editor role serves 154 with 0 running_game_*, so these replies cannot come from the editor endpoint."
    },
    {
      "id": "E4",
      "pass": true,
      "evidence": "evidence.json parses: qa_status=partial, verified_records=10 (F1,F2,F3,F5,F10,F13,F16,N1,N2,N3), gap_records=13 (F2b,F4,F6,F7,F8,F9,F11,F12,F13b,F14,F15,F17,N3b), overlap [], no duplicate ids; every execution_record path exists in iter-1/candidate (MISSING=[]); all record candidate_ids = a54179ce...; every gap has player_impact and recommended_update; planner_handoff 4/9/3. See defect T13A-4 for the wrong verified-only/gap-only execution-record split."
    },
    {
      "id": "E5",
      "pass": true,
      "evidence": "My own manifest comparison: versions/a54179ce..., iter-1/candidate and .workspace/fresh-t13 each 13 files / 9610 B with the same tree id a54179ce...; only_in=[] differing=[]; result.json candidate_id == version_id == a54179ce.... QA did not modify A1."
    },
    {
      "id": "E6",
      "pass": true,
      "evidence": "qa_report.md line 3 is literally '## Verdict: partial'; it enumerates the 13 gap families, and line 31 states 'input_axis is not a real observable (DR-58); assert on positions/properties'. No unmet item is reported as verified."
    },
    {
      "id": "REPRO-COMMAND-SEQUENCE",
      "pass": true,
      "evidence": "Verbatim: init.txt and round_console2.txt carry init and run command lines that differ from TASK-SMOKE-T12-REPORT.md lines 8-9 only in the run id (smoke-t12/smoke-t13) and project dir (fresh-t12/fresh-t13), plus one extra space in T12's init line (T12: 'init  --project', T13: 'init --project'), which the report discloses; the engine launch line differs only in --path."
    },
    {
      "id": "REPRO-INVARIANTS",
      "pass": true,
      "evidence": "Independently recomputed on both rounds: E1..E6 all met; start_state fresh in both (smoke-t12 meta.json and smoke-t13 meta.json); artifact_gate applicable+launchable reasons=[] in both; four behaviour classes each carry an engine-side passing assertion in both (T12 battery.json: 4 POSITION_ASSERT_PASSED + 2 running_game_assert_node_state passed=true; T13 the same); exit codes agree; A0 identical across t11/t12/t13 (3ac25f6c..., project.godot 00d02c9c...); A1 != A0 with the change on engineering files in both; all ten read-only baselines byte-identical under my own culture-order digest validated on runs/smoke-t6 = c144ef32...7a9c03."
    },
    {
      "id": "REPRO-NONREPRODUCED-HONEST",
      "pass": true,
      "evidence": "The non-reproduced items are quantified and the T12 side of each delta is true when re-read from runs/smoke-t12: A1 fc50ecd2... 11 files/7384 B; tokens 17,703,610 with attempt sum 17,252,776 and planner summary 90/901,668 vs attempt 45/450,834; developer attempts 150+25 both LimitsExceeded artifact_valid=false with wrap_up_retry_used=true; scene 22 nodes; move_right +216.333313; move_left -216.332458; gap ids [F1-stop,F6,F7,F8,F9,F11,F12,F14,F15,F17]; verified 12. T13 side re-read from runs/smoke-t13 matches as well. The run-to-run flip is additionally mischaracterised (see T13A-1)."
    },
    {
      "id": "LIVE-ROUTE-EXERCISED",
      "pass": true,
      "evidence": "Tester attempt1 messages 151-155: four 'hoh tools call running_game_get_node_properties' with returncode 0 and real node-property replies ({'/root/Main/HUD/Result' text:''}, {'/root/Main/Player' facing/position/velocity}, {'/root/Main/Goal' reached:false}, {'/root/Main/HUD/Coins' text:'Coins: 0'}) at 05:00:12-05:00:31. Developer attempt2 messages 137-139: one 'tools call running_game_get_scene_tree' at 04:51:28 with returncode 5 and the DR-43 refusal text. My census over the four unredacted final trajectories reproduces the report line by line: 29/0/0, 187/23/0, 98/47/1, 134/8/4; totals 448 executed commands, 78 tools call, 5 running_game_* (4 success, 1 refusal), 0 editor_play_scene."
    },
    {
      "id": "LIVE-ROUTE-CAUSAL-EXPLANATION",
      "pass": false,
      "evidence": "The outcome direction is right (no route at the 04:51:28 refusal, a live route at the 05:00 successes) but the stated cause is false. See defect T13A-1: the round's initial game start succeeded and published http://127.0.0.1:53068/mcp (probed by the round author at 04:19:22; the same :53068 game console appears in developer.attempt2 message 77 at 04:44:02); warnings.log was last written at 04:41 (message 135's dir listing: 1110 B = qa_scope + DR-70 only), so the DR-70 failure is a LATER start, not the 04:17:44 round start. The alternative 'the difference was the tool' is refuted: running_game_get_scene_tree was refused at 04:51 and the same tool succeeded inside battery pass 2 on :51223; the alternative 'the difference was the role' is refuted: the battery's own non-role caller gets the identical DR-43 text when no route is registered, and both roles inherit the same HOH_GAME_ROUTE."
    },
    {
      "id": "UNEXERCISED-BRANCH",
      "pass": true,
      "evidence": "My census finds 0 'editor_play_scene' invocations across the four unredacted final trajectories (negative control: the detector fires on a synthetic 'tools call editor_play_scene' and does not fire on a plain mention of running_game_ inside an analysis command). src/prompts/developer.md:113 and :142 do forbid it ('do not start a game of your own (editor_play_scene)'); src/prompts/tester.md:18 demotes self-collection to secondary. So the DR-78 republish branch cannot be walked naturally under the current prompts."
    },
    {
      "id": "DOUBLE-COUNT-MECHANISM",
      "pass": true,
      "evidence": "I re-implemented the runtime filter (usage.rs:130: name.starts_with('<role>.attempt') && name.ends_with('.json')) and extract_usage/merge_usage over exactly the files it matches: planner.attempt1.json (27 calls/272,378) and planner.attempt1.redacted.json (27/272,378) merge to 54 calls/544,756, byte-equal to the runtime summary. Runtime total 15,123,294 - attempt sum 14,850,916 = 272,378. History from the raw trees: t10 planner ratio 1.000 (no sidecar), t11 1.000 (only developer.attempt1.redacted.json, and the developer entry is built by merging attempts), t12 2.000, t13 2.000. The timing is the mechanism: the planner's redaction sweep (run_loop.rs:965) runs before usage_from_attempts (run_loop.rs:982), while the tester's (run_loop.rs:1675) runs after (run_loop.rs:1672), which is why the tester's own sidecar does not double-count."
    },
    {
      "id": "DEV-ATTEMPT-MECHANISM",
      "pass": false,
      "evidence": "Half true, half false. True: attempt2 is the DR-70 launch-gate repair (developer.attempt2.log notes 'launch_gate_repair: the pre-freeze launchable gate failed'; repair_retry_used=true, wrap_up_retry_used=false), and developer_artifact_valid_in does inspect the main scene's existence, structure, script references and non-empty script files. False: the report's looseness account (T13A-3) attributes attempt2's flag to reuse of attempt1's value via run_loop.rs:1185, but that line is inside the wrap-up block that did not fire; the repair block sets artifact_valid: workspace.is_dir() at run_loop.rs:1378, which is unconditionally true."
    },
    {
      "id": "64KIB-MECHANISM",
      "pass": false,
      "evidence": "The report's '0 occurrences in the four unredacted trajectories' is false. See defect T13A-2."
    },
    {
      "id": "GUARDS-BASELINES",
      "pass": true,
      "evidence": "My own PowerShell digest (Get-ChildItem -Recurse -Force -File; repo-root-relative lowercase POSIX path + TAB + bytes + TAB + sha256; culture-order Sort-Object; LF-joined with no trailing newline; SHA-256 of the UTF-8 bytes) reproduces the task book's anchor runs/smoke-t6 = 135 files / c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03 / newest 2026-09-29 02:32:01, and all ten current digests equal the report's table (t6 135/c144ef32, t7 115/6e4c1595, t8 358/6d11b2c6, t9 83/541e2d81, t10 232/31955589, t11 186/a76c228f, t12 215/1d5889b7, mario 178/dee0a36f, fresh-t11 100/4c07c0b6, fresh-t12 109/da56639b). Ordering matters (mario: culture dee0a36f vs ordinal f622f5b0; t9: culture 541e2d81) and path prefix matters (t9 with subtree-relative paths = 0834b988...)."
    },
    {
      "id": "FROZEN-AND-HYGIENE",
      "pass": true,
      "evidence": "PRD-mario.md sha256 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a; DECISIONS.md sha256 eb7090086c454966445518978606f35cf6ee3e1cba61c2d4601a86c5f548a7c2 (identical to the value the T12 acceptance measured, so the round added no D entry); nested engine godot-mcp/godot HEAD fc63af77c33368c4a1bb839c95d19750554f63a3 with an empty porcelain; engine binary sha256 08483088...e9e6a, size 194216960, mtime 1790641862 (same as T12); Cargo.toml/Cargo.lock untouched by 8ddbad3..HEAD (no new dependencies); the two round commits touch only .spec/hof-rs/tasks/TASK-SMOKE-T13-REPORT.md; origin/master is still 8ddbad3f... so nothing was pushed."
    },
    {
      "id": "MACHINE-BLOCK",
      "pass": true,
      "evidence": "Line-anchored fence scan finds exactly one 'json' block (lines 741-1408); it json.loads to 29 top-level keys; its text plus the file's single trailing newline is byte-identical to runs/smoke-t13/evidence/analysis/machine_block.json (34699 B, sha256 36e34d0d...c3c9f). Caveat: two inline '```' sequences in prose (lines 658-659) break naive split('```') parsers; the report's own fence count of 64 is line-anchored and correct."
    },
    {
      "id": "CITE-EXISTENCE",
      "pass": true,
      "evidence": "Every one of the 187 path-like backticked tokens listed in cite_check.txt resolves under the report's ten contexts or by basename (I re-resolved all 187 myself: 0 unresolved), and the tokens the report's checker skipped (the four *.redacted.json sidecars, scenes/main.tscn, config/model.secret.env) exist too. One evidence-index row is stale (see T13A-6)."
    },
    {
      "id": "UTF8-AND-LEAK",
      "pass": true,
      "evidence": "I decoded every file under runs/smoke-t13 and .workspace/fresh-t13 (373 files) and under the out-of-repo staging dir (84 files): the only non-UTF-8 files are binaries (11 PNG + 1 .pyc + .godot/uid_cache.bin; plus the staging .pyc). I loaded the 51-byte HOH_MODEL_API_KEY from config/model.secret.env and scanned for its value: 0 hits. Independent caveat: a non-secret environment value DID leak (see T13A-5)."
    },
    {
      "id": "COUNTS-SCOPED",
      "pass": false,
      "evidence": "Several counts do not recompute: see defects T13A-4, T13A-6, T13A-7."
    }
  ],
  "defects": [
    {
      "id": "T13A-1",
      "severity": "major",
      "what": "The round's central causal account of the live-route behaviour is wrong. The report says the round's own game session start failed at 04:17:44 with endpoint :55361 and that no published route existed for any role until battery pass 2. Raw evidence shows the round's initial start succeeded and published http://127.0.0.1:53068/mcp, which the round author probed at 04:19:22 (runs/smoke-t13/evidence/round/game_endpoint_tools_list_round_author.json and game_endpoint_scene_tree_round_author.json both address :53068 and carry valid replies), and whose console line '[MCP] role=game configured_port=53068' the developer read at 04:44:02 (developer.attempt2.json message 77). warnings.log was last written at 04:41 (developer.attempt2.json message 135 dir listing: 1110 B = the qa_scope line 212 B + the DR-70 line 896 B + newline, mtime 04:41), so the DR-70 line was appended at ~04:41, not 04:17:44; the only start_round_game call that can fail then is the repair retry (src/runtime/run_loop.rs:1348, which runs right after battery pass 1 failed at 04:41:30-04:41:38), whose editor_play_scene answered :55361. Consequences: the run-to-run 'invariant that flipped' and the risk statement 'the promise and the behaviour disagree ... for the whole window' are overstated; the route was live during the Planner and Developer attempt 1. The report's §3.3(d) timeline also places the developer's refusal at 04:31:28 although its own §3.3(b) locates it in attempt 2 and the message timestamp is 1790887888.17 = 04:51:28.",
      "reproduction": "grep 53068 runs/smoke-t13/evidence/round/*.json -> two files POST http://127.0.0.1:53068/mcp; python: developer.attempt2.json msg 134/135 output contains 'no route file' AND warnings.log 1110 B at mtime 04:41; epochs.txt anchors 1790888078=04:54:38 so 1790887888=04:51:28; read src/runtime/run_loop.rs:827-832 (initial start), 1306 (stop before battery), 1348 (repair start), 1427 (post-battery start)."
    },
    {
      "id": "T13A-2",
      "severity": "major",
      "what": "The report claims the 64 KiB output-truncation path was never triggered ('warnings.log ... four unredacted trajectories hoh_output_truncated 0 times', machine block truncation_64kib.triggered=false, F-T13-4 'still untriggered'), but it WAS triggered once: tester.attempt1.json message 98 (a tool reply at 04:56:37 to a command that dumped .hoh/deterministic/raw/interaction_evidence.json) carries extra.hoh_output_truncated=true, hoh_output_limit_bytes=65536, hoh_output_original_bytes=81139, and the runtime's own marker text '[hoh: 65536 of 81139 bytes were carried; the remaining 15603 bytes were dropped ...]'. This is the first real-machine exercise of that path, and the report both misses it and reports the opposite.",
      "reproduction": "python: for each of the four unredacted trajectories walk messages and print extra['hoh_output_truncated'] -> tester.attempt1.json msg 98 True (limit 65536, original 81139), all others absent."
    },
    {
      "id": "T13A-3",
      "severity": "medium",
      "what": "The artifact_valid looseness is attributed to the wrong code path. The report says attempt 2's flag reuses attempt 1's value (run_loop.rs:1137 computed once, 1185 reused) and cites a source reading of run_loop.rs:1137/1185. Line 1185 is inside the wrap-up-retry block guarded by 'developer_limits && !developer_artifact_valid', which did not fire (wrap_up_retry_used=false). T13's attempt 2 comes from the DR-70 launch-gate repair block, whose AttemptOutcome sets artifact_valid: workspace.is_dir() at line 1378 - an always-true check, not a reused one. The conclusion that the flag is loose is right, but for a stronger and different reason than reported.",
      "reproduction": "grep -n artifact_valid src/runtime/run_loop.rs -> 1137, 1147, 1154, 1185, 1378; read 1343-1398 (repair block, line 1378) vs 1154-1188 (wrap-up block)."
    },
    {
      "id": "T13A-4",
      "severity": "minor",
      "what": "E4's execution-record split is mislabelled: the report (and machine block count_scopes 'entries inside verified_records only'/'inside gap_records only') says verified-only=10 and gap-only=13. In evidence.json the 10 verified records carry 21 execution_records and the 13 gap records carry 10; the total 31 is correct. The record-type table {replay:11, runtime_trace:10, build:5, assert:3} sums to 29 and omits screenshot:2.",
      "reproduction": "python: sum(len(r['execution_records']) for r in d['verified_records']) = 21; for gap_records = 10; types {\"replay\":11,\"assert\":3,\"runtime_trace\":10,\"screenshot\":2,\"build\":5}."
    },
    {
      "id": "T13A-5",
      "severity": "minor",
      "what": "An environment value leaked into the frozen round evidence: roles inherit the harness shell environment, and 'env | grep -i hoh' / the env dump echoed DSH_TERM_CMD, which contains the round author's controlling command line including the out-of-repo staging path F:\\moonbit-hof-rs-t13-staging and the name config/model.secret.env. It appears in planner.attempt1.json and developer.attempt1.json and their redacted sidecars. The 51-byte key value itself did NOT leak (0 hits). The report's secret-scan is scoped to the key value and does not cover this vector, so the claim 'no environment value leaked' is not fully supported.",
      "reproduction": "grep -rl DSH_TERM_CMD runs/smoke-t13/ -> planner.attempt1.json, planner.attempt1.redacted.json, developer.attempt1.json, developer.attempt1.redacted.json; developer.attempt1.json msg 8/9 (04:18:26) 'env | grep -i hoh'."
    },
    {
      "id": "T13A-6",
      "severity": "minor",
      "what": "Counts do not recompute in several places. Report 11.4: 'copied in 106 files: round 23 / analysis 28 / gatecheck 5 / scripts 50' (sums to 106) but the tree holds 110 (23/31/5/51). Report 12: 'evidence/scripts/** (37 files ...)' and 'evidence/analysis/** (14)' against 51 and 31 in reality and 51 in the machine block. Machine block count_scopes: round_dir_files 264 (actual 268), round_dir_files_before_evidence 147 (actual 158); 147+110 != 264. Evidence index: cite_check.txt is listed as 18189 B but is 18401 B (the other 58/59 rows match exactly, size and sha256 prefix).",
      "reproduction": "find runs/smoke-t13 -type f | wc -l = 268; find runs/smoke-t13/evidence -type f = 110; per-subdir 23/31/5/51; python index.py over the report's evidence tables -> 1 mismatch (cite_check.txt)."
    },
    {
      "id": "T13A-7",
      "severity": "info",
      "what": "warnings.log is described as '8 lines' in the mechanism table; the file has 7 newline-terminated lines (splitting on LF yields 8 pieces because of the trailing newline).",
      "reproduction": "python: open(warnings.log,'rb').read().split(b'\\n') -> 8 elements, last empty; wc -l -> 7."
    },
    {
      "id": "T13A-8",
      "severity": "info",
      "what": "The report classifies as an inference ('strong inference, ~0.85; I never stat-ed the file at that moment') the fact that no route file existed when the developer was refused. In fact the developer's own command 43 s earlier directly tested it: 'if exist \"%HOH_GAME_ROUTE%\" (type ...) else (echo no route file)' printed 'no route file' at 04:50:46 (message 134->135). The unverified list is therefore over-conservative on this point (and, given T13A-1, still mis-sited on the round-game-start item).",
      "reproduction": "developer.attempt2.json msg 134 command and msg 135 output tail '===ROUTE=== \\nno route file'."
    },
    {
      "id": "T13A-9",
      "severity": "minor",
      "what": "Three untracked temporary files the developer left in the repository root (.tmp_coin.json 108 B, .tmp_goal.json 68 B, .tmp_hud.json 46 B, mtime 04:52:28-29) are still present and keep git status dirty. They come from developer.attempt2 message 143, after that role deleted its earlier temp files at message 140 ('del .tmp*.json' printed File Not Found for the rest). The runtime lists them under result.json.out_of_tree_writes (detected, not prevented). Not a criterion failure; a small hygiene fix (make the developer write temp args under the scratch dir, or have the runtime clean/report them at close) is warranted.",
      "reproduction": "git status --porcelain -> the three ?? entries; stat sizes/mtimes; python developer.attempt2 msgs 140/143."
    }
  ],
  "risks": [
    "The role-visible game route is published by whichever start_round_game call succeeded last; the round-start one can succeed while the repair-time restart fails, so 'the runtime publishes that route for the whole round' (developer prompt, developer.md:33) is not guaranteed even in a round whose initial start worked - and the T13 report's own account of this is wrong.",
    "The 64 KiB output cap now fires on real 81 KB payloads (deterministic raw records), so a role that dumps raw evidence loses the tail from its own view; the runtime does append a marker, but any analysis that trusts a role's in-context view will silently miss evidence.",
    "The harness shell environment reaches role shells (DSH_TERM_CMD here). Today it carries only paths and a command line; if a secret ever appears on the harness command line it will be captured into frozen trajectories and redaction copies.",
    "Any downstream reading of the T13 report inherits the wrong :55361/04:17:44 timeline and the false '64 KiB never triggered' claim.",
    "Untracked .tmp files in the repository root keep accumulating; the out-of-tree watcher reports but does not prevent writes, and these files are not part of any baseline, so they can slip through hygiene checks."
  ],
  "unverified": [
    "The empty-directory proof is a self-authored capture (run 04:10:01) that cannot be re-derived offline; what I could verify independently is that A0 is the deterministic scaffold identical to smoke-t11/12 and that start_state.mode=fresh, the versions index holds only iterations 0 and 1, and only one iter-1 directory exists.",
    "I did not instrument the engine: the attribution of the failed DR-70 start to the repair-time call (run_loop.rs:1348) rather than to the round-start call (run_loop.rs:832) is inferred from warnings.log's mtime at 04:50:45 (04:41), the fact that plan.md/developer attempt 1 begin at 04:18, and the code order; it is strong but not direct.",
    "I could not stat the game_endpoint.json file directly (it is withdrawn at close); the proof that a live route existed at 04:19:22 is the round author's own two probes of http://127.0.0.1:53068/mcp, not a file mtime.",
    "Whether the 04:19:22 :53068 game and the 04:41 :55361 start were the only two between the round start and pass 2 (no per-start log exists; only the single DR-70 warning and the two battery passes are recorded).",
    "Redaction sidecar fidelity: the four *.redacted.json copies parse and their originals are byte-unchanged, but I did not diff what was removed.",
    "The exact semantics/limits of out_of_tree_writes beyond the three paths it lists (I read result.json only, not the watcher's verification logic).",
    "The staging bundle's completeness: F:\\moonbit-hof-rs-t13-staging still exists (84 files, 83 text, all valid UTF-8, no key value) but I did not prove that every staging file was copied into runs/smoke-t13/evidence.",
    "I did not pixel-analyse the 11 PNGs (only sizes/magic were relevant), and I did not start the engine or any round."
  ],
  "not_checked": [
    "I did not start the engine, run a round, or use the network (offline constraint); no file under runs/** was written by me.",
    "I did not read the whole of src/**; I read only the paths the report's claims depend on (usage.rs, run_loop.rs, godot.rs, policy.rs, prompts).",
    "I did not rebuild target/release/hoh.exe; freshness rests on sha256 310075fa...7158ca and mtime 02:45:40 matching the T12 record with only docs changed since.",
    "I did not verify the content of the A0 scaffold beyond hashes/sizes.",
    "I did not re-derive the editor/godot process liveness at close (pid 948) - the round is over."
  ],
  "plants_and_counterexamples": [
    "Digest scheme self-validation and sensitivity: my own culture-order PowerShell digest reproduces the task book anchor runs/smoke-t6 = 135 / c144ef32...7a9c03 / 2026-09-29 02:32:01 and all ten baselines; a subtree-relative-path variant on runs/smoke-t9 gives 0834b988 instead of 541e2d81 (path prefix is load-bearing); an ordinal sort of .workspace/mario gives f622f5b0 instead of dee0a36f (ordering is load-bearing).",
    "Tree-hash re-implementation: my own relpath/len/bytes stream reproduces 3ac25f6c... (3/1727) and a54179ce... (13/9610) and the three-tree equality, so the A0->A1 increment is real and lies on engineering files.",
    "Usage double-count re-implementation: the runtime's own filter matches exactly two planner files, both carrying the same usage, and their merge equals the runtime summary (54/544,756) - so the 2x is a file-selection defect, not two model calls.",
    "Tool-name detector negative control: the regex matches synthetic 'tools call running_game_get_scene_tree' / 'tools call editor_play_scene' and does not match a bare mention of running_game_ inside an analysis command, so the observed zeros are true negatives.",
    "Endpoint-attribution counterexample: the editor role serves 154 tools with 0 running_game_*; the game role serves 73 with 0 editor_*, so the game-endpoint readings cannot come from the editor.",
    "Truncation counterexample: parsing extra.hoh_output_truncated instead of grepping the raw byte text finds 1 real truncation (81139 -> 65536) that the report reports as 0.",
    "Route-state counterexample to the report's timeline: the round author's own 04:19:22 POSTs to :53068 (unknown to the report) show a live published route during Developer attempt 1, which refutes 'no route for any role until battery pass 2' and the 04:17:44 failure time.",
    "Inline-fence trap: split('```') reports 33 blocks / 2 'json' blocks because two prose lines contain literal triple backticks; a line-anchored scan finds 64 fences and exactly one json block, matching the report's self-check."
  ]
}
```

<!-- 验收自证（由生成脚本在回读成功后追加） -->

## 0. 判定摘要

| 项 | 判定 | 一句话依据 |
|---|---|---|
| 六条判据 E1..E6 | **全部 pass（我逐条复算）** | A0=3ac25f6c(3/1727)、A1=a54179ce(13/9610)、三棵树逐字节同一；28 节点、金币 0→2、Goal false→true、四发 `POSITION_ASSERT_PASSED` + 两发 `running_game_assert_node_state passed=true`；`evidence.json` 10/13；`qa_report.md` 逐字 `Verdict: partial` |
| 复现轮标题答案 | **支持** | 命令逐字相同（仅 run id / 工程目录 + T12 那一个多余空格）；不变量逐条再次成立；未复现项如实量化（我用 T12 原始件逐条复核了 t12 一侧） |
| 角色 live 游戏路由 | **调用发生了（4 成功 / 1 被拒）** | Tester 4 次 `running_game_get_node_properties` exit 0；Developer 1 次 `running_game_get_scene_tree` exit 5（DR-43） |
| 因果解释 | **fail** | 报告说轮内起游戏在 04:17:44 失败、到 pass 2 之前无路由；实测轮内首次起游戏**成功**并发布了 `:53068`，作者 04:19:22 亲自探过它（`T13A-1`） |
| 未走到的分支 | **成立** | 四个未脱敏轨迹 `editor_play_scene`=0；`developer.md:113/:142` 明令禁止角色自起场景 |
| usage 双计 | **机制复现** | 用运行时的过滤器复算，两个 planner 文件合起来恰是 summary；T12 同病、T10/T11 干净 |
| developer 尝试机制 | **一半错** | attempt2 确是启动门修复；但 `artifact_valid` 不是复用（`T13A-3`） |
| 64 KiB | **报告说反了** | 真机触发过一次：Tester msg 98，81139→65536（`T13A-2`） |
| 十条只读基线 | **逐字节未变** | 我自写 culture-order 口径先命中 t6 锚点 `c144ef32…7a9c03`，10/10 与报告表一致 |
| 冻结件/引擎/Cargo/push | **未动** | PRD `4c81c3a9…`；`DECISIONS.md` `eb709008…`（= T12 值）；嵌套引擎 `fc63af77…` porcelain 空；Cargo 无改动；`origin/master` 仍 `8ddbad3` |
| 机器可读块 | **合法且逐字节同一** | 行锚定扫描：1 个 json 块、29 键、`json.loads` 通过、正文+尾换行 == `machine_block.json`（34699 B） |

**总判定：`fail`（范围见 `verdict_scope`）**——六条判据与复现结论都成立且被我独立复算；失败的是本报告自己的报告纪律与机制归因：三处机制断言与原始件冲突（轮内起游戏的归因、64 KiB、`artifact_valid`），若干计数不可复算。**不需要重跑轮次，需要改报告与机制章节。**

> 口径声明：本报告所有数字来自我自己跑的脚本或直接读取的原始件；被验收报告只用于**定位**。全程离线，未启动引擎、未跑任何轮、未联网；**未写 `runs/**`**（连临时文件也没有）；未改任何工作区、冻结规范、`DECISIONS.md`、`godot-mcp/**`；未 push、未 stage；临时材料全在仓库外 `C:\Users\wyl\AppData\Local\Temp\t13acc`；**未使用 `rm -rf`**、未从未展开变量构造路径。

## 1. 逐项核对表

| # | 要求 | 我的独立读数 | 结论 |
|---|---|---|---|
| 1 | 命令序列与 T12 相同（除 run id / 工程目录） | `init.txt`/`round_console2.txt` vs T12 报告第 8-9 行：仅 id/dir 不同，T12 的 init 行多一个空格（报告已披露）；引擎启动行仅 `--path` 不同 | **成立** |
| 1b | 本轮目录确为空、先 `init` 后单轮 | 空目录清单是 04:10:01 的自述件；`A0` 与 T11/T12 同 sha（确定性脚手架）；`start_state.mode=fresh`；`versions/index.json` 只有 iteration 0(init)/1(developer)；`iter-1` 只有一个；`result.json.attempts` 4 条；`round_console.txt`：04:14:36 exit 2 / 0.412 s 被拒（`runs/smoke-t13` 已存在） | **成立（空清单不可复导，见 §4）** |
| 2 | 各不变量再次成立 | E1..E6 全 met；fresh；门 `launchable=true,reasons=[]`；四类行为各有引擎侧 `passed=true`；退出码 `30 0A`/`0`/`30 0A`/wrapper 0；A0 与 T12 逐字节相同；10 条基线未变 | **成立** |
| 2b | 未复现项如实量化 | `A1` fc50ecd2(11/7384) vs a54179ce(13/9610)；tokens 17,703,610 vs 15,123,294；墙钟 2144 s vs 2780.2 s；场景 22 vs 28；move_right +216.333313 vs +21.082520；gap 集合不同；attempt 形态不同 —— 我逐条从 T12/T13 原始件复核 | **成立** |
| 3 | 角色 live 调用真的发生 | Tester msgs 151-155 四次 exit 0 + 真实属性回包；Developer msgs 137-139 一次 exit 5 + DR-43 原文；我复算 448/78/5/0 | **成立** |
| 3b | 两种命运的因果 | 结果为真（拒时无路由、Tester 时有路由），**归因为假**（`T13A-1`）；反例检验：同工具在 pass 2 成功、同一 DR-43 文本也出现在运行时自己的失败里、两角色同一 `HOH_GAME_ROUTE` | **部分成立（因果归因错）** |
| 4 | 未走到的分支 | `editor_play_scene`=0（负控通过）；`developer.md:113/:142` 逐字禁止 | **成立** |
| 5 | 双计机制 | 复算 `54/544,756` == summary；`usage.rs:130` 过滤器；T12 ratio 2.0、T10/T11 1.0；时序解释（planner sweep 在 `usage_from_attempts` 之前、tester 之后） | **成立** |
| 5b | developer 尝试机制 | `repair_retry_used=true`/`wrap_up=false`、日志 notes 逐字是启动门修复；**但** `artifact_valid` 的漏洞被指到没执行的 wrap-up 分支（`T13A-3`） | **部分成立** |
| 6 | 六条判据判定与诚实性 | 见 §0；无 unjudgeable；E6 主动拒绝把 `input_axis` 当观测 | **成立（判据本身）** |
| 7 | 十条基线 | culture-order 口径自证 t6 锚点；10/10 命中；序数/子树前缀会改值 | **成立** |
| 8 | 机器可读块 | 行锚定 1 个 json 块、`json.loads` 通过、与 `machine_block.json` 同字节 | **成立** |
| 9 | 引用存在性 | 187 个 token 在 10 个上下文/按 basename 全部可解析；被跳过的 `.redacted.json` 等也存在 | **成立** |
| 10 | UTF-8 / 无密钥泄漏 | 373+84 个文件：非 UTF-8 全是二进制；51 字节密钥值 0 命中；**但** `DSH_TERM_CMD` 泄漏进轨迹（`T13A-5`） | **成立（有附带发现）** |
| 11 | 计数作用域 | 多处不可复算（`T13A-4/6/7`） | **不成立** |
| 12 | 披露的三起自伤 | 被拒启动（`round_console.txt` exit 2）；注入器 0 字节（现存两份 `ROLE_NOTE-t13.md` 均 1586 B）；在途普查把 Tester 数少（`game_route_calls_inflight.txt` 85/0 vs 最终 134/4） | **披露属实** |
| 13 | 越界写入 | 3 个 `.tmp_*.json` 实测存在（108/68/46 B，04:52:28-29，未跟踪）；来自 attempt2 msg 143，此前 msg 140 删过一轮 | **成立（`T13A-9`）** |

## 2. 我自己做的植入与反例

- Digest scheme self-validation and sensitivity: my own culture-order PowerShell digest reproduces the task book anchor runs/smoke-t6 = 135 / c144ef32...7a9c03 / 2026-09-29 02:32:01 and all ten baselines; a subtree-relative-path variant on runs/smoke-t9 gives 0834b988 instead of 541e2d81 (path prefix is load-bearing); an ordinal sort of .workspace/mario gives f622f5b0 instead of dee0a36f (ordering is load-bearing).
- Tree-hash re-implementation: my own relpath/len/bytes stream reproduces 3ac25f6c... (3/1727) and a54179ce... (13/9610) and the three-tree equality, so the A0->A1 increment is real and lies on engineering files.
- Usage double-count re-implementation: the runtime's own filter matches exactly two planner files, both carrying the same usage, and their merge equals the runtime summary (54/544,756) - so the 2x is a file-selection defect, not two model calls.
- Tool-name detector negative control: the regex matches synthetic 'tools call running_game_get_scene_tree' / 'tools call editor_play_scene' and does not match a bare mention of running_game_ inside an analysis command, so the observed zeros are true negatives.
- Endpoint-attribution counterexample: the editor role serves 154 tools with 0 running_game_*; the game role serves 73 with 0 editor_*, so the game-endpoint readings cannot come from the editor.
- Truncation counterexample: parsing extra.hoh_output_truncated instead of grepping the raw byte text finds 1 real truncation (81139 -> 65536) that the report reports as 0.
- Route-state counterexample to the report's timeline: the round author's own 04:19:22 POSTs to :53068 (unknown to the report) show a live published route during Developer attempt 1, which refutes 'no route for any role until battery pass 2' and the 04:17:44 failure time.
- Inline-fence trap: split('```') reports 33 blocks / 2 'json' blocks because two prose lines contain literal triple backticks; a line-anchored scan finds 64 fences and exactly one json block, matching the report's self-check.

## 3. 独立判断

1. **复现轮的标题答案成立。** 命令是同一序列，E1..E6 的判定类别、`start_state=fresh`、门的开启、四类行为各有一发引擎侧通过断言、退出码、A0 身份、十条基线都再次成立；未复现项（A1 身份、tokens、墙钟、坐标、gap 集合、attempt 形态）都被如实量化，且我逐条回读 T12 原始件确认了那些「上一轮一侧」的数字。
2. **但本轮自己最重要的新观测被讲错了。** 报告把「轮内起游戏失败」定在 04:17:44、端点 `:55361`，并据此说「到电池 pass 2 之前任何角色都没有可采纳的路由」。轮内证据（作者 04:19:22 对 `:53068` 的两次 POST、Developer 04:44:02 读到的 `role=game configured_port=53068`、`warnings.log` 在 04:41 才被写入）表明：**首次起游戏是成功的**，失败发生在修复重试那次起游戏。这不改变轮次结论，但改变「不变量翻转」与风险叙述。
3. **64 KiB 截断路径本轮首次真机触发**，报告写成了「未触发」。一个 81 KB 的确定性原始件被截到 64 KB，运行时自己的标记就在轨迹里。这条恰好是被验收报告点名的「0 次」纪律的反例。
4. **`artifact_valid` 的说法要去修**：本轮 attempt2 的该字段来自 `run_loop.rs:1378` 的 `workspace.is_dir()`（恒真），不是 `:1185` 的复用；报告引的行号属于没触发的 wrap-up 分支。
5. **角色侧 live 游戏路由能用**：Tester 4 次成功是真机正面读数；「被拒」与「可用」都不是 CLI 的属性，而是调用时刻路由状态的属性——这一点报告的 C-D 反例是对的。
6. **未走到 `editor_play_scene` 分支是结构性的**：提示词明令禁止，所以该分支不可能被自然走到；报告把它列为「仍需显式授权/专用探针」是诚实且正确的。
7. **诚实性总体良好但不够**：被拒启动、注入器崩溃、在途普查都主动披露，且 `artifact_valid=true`、pass 1 失败、DR-70 都没有藏。但三处机制断言与原始件冲突，其中一处（64 KiB）是硬「0 次」断言失败，故按本批自己的报告纪律不能给 pass。

## 4. 未证实项（附理由）

- The empty-directory proof is a self-authored capture (run 04:10:01) that cannot be re-derived offline; what I could verify independently is that A0 is the deterministic scaffold identical to smoke-t11/12 and that start_state.mode=fresh, the versions index holds only iterations 0 and 1, and only one iter-1 directory exists.
- I did not instrument the engine: the attribution of the failed DR-70 start to the repair-time call (run_loop.rs:1348) rather than to the round-start call (run_loop.rs:832) is inferred from warnings.log's mtime at 04:50:45 (04:41), the fact that plan.md/developer attempt 1 begin at 04:18, and the code order; it is strong but not direct.
- I could not stat the game_endpoint.json file directly (it is withdrawn at close); the proof that a live route existed at 04:19:22 is the round author's own two probes of http://127.0.0.1:53068/mcp, not a file mtime.
- Whether the 04:19:22 :53068 game and the 04:41 :55361 start were the only two between the round start and pass 2 (no per-start log exists; only the single DR-70 warning and the two battery passes are recorded).
- Redaction sidecar fidelity: the four *.redacted.json copies parse and their originals are byte-unchanged, but I did not diff what was removed.
- The exact semantics/limits of out_of_tree_writes beyond the three paths it lists (I read result.json only, not the watcher's verification logic).
- The staging bundle's completeness: F:\moonbit-hof-rs-t13-staging still exists (84 files, 83 text, all valid UTF-8, no key value) but I did not prove that every staging file was copied into runs/smoke-t13/evidence.
- I did not pixel-analyse the 11 PNGs (only sizes/magic were relevant), and I did not start the engine or any round.

### 4b. 对被验收报告「未验证/推断」清单的裁定

| 报告条目 | 我的裁定 |
|---|---|
| 引擎是否总需要 >10 s 绑定游戏端口 | **仍未定**；补充一个数据点：轮内首次起游戏（`:53068`）是**成功**的，所以「三次里两次失败」应改成「四次里两次失败、两次成功」 |
| `:55361` 那个游戏进程的寿命 | **条目本身错位**：`:55361` 不是「最初的」轮内游戏端点；最初的是 `:53068`（`T13A-1`） |
| 为什么轮内起游戏与 pass 1 失败而 pass 2 成功 | **部分回答**：轮内首次起游戏并没有失败；失败的是修复重试那次起游戏与 pass 1。根因（绑定慢/轮询紧）仍未定 |
| DR-78 角色自起场景重发布分支未走到 | **成立**：0 次 `editor_play_scene`，提示词禁止（已由我复算） |
| `out_of_tree_writes` 的语义 | **未验证**（我只读了 `result.json` 的字段） |
| 脱敏旁路副本的内容保真 | **未验证**（未 diff 差异） |
| `artifact_valid` 在修复尝试上的源码语义 | **我已读源码**：不是复用，是 `workspace.is_dir()`（`T13A-3`）；报告的这条「未验证」可以直接关闭为「已查明，报告写错」 |
| 64 KiB 截断仍未触发 | **为假**：本轮触发过一次（`T13A-2`） |

### 4c. 隔离的电池 pass 1 裁定

`runs/smoke-t13/quarantine/deterministic-pass-1.stale-1790888078/**` 实测存在且完整（12 个 raw + `mcp-sync.json` + `mcp-errors.jsonl`）：`play_scene_ready` 的 `editor_play_scene` 应答 `:55336`（pid 10676），随后 `running_game_get_scene_tree` 在 1790887290/1790887297 两次连接被拒、1790887298 被标记 unavailable；`battery_passes` 里 pass 1 `launchable=false`、pass 2 `launchable=true`，与 12 步 ok 矩阵一致。**隔离机制正常、原始件保留、报告对该段的引用属实。**

## 5. 我没有检查的

- I did not start the engine, run a round, or use the network (offline constraint); no file under runs/** was written by me.
- I did not read the whole of src/**; I read only the paths the report's claims depend on (usage.rs, run_loop.rs, godot.rs, policy.rs, prompts).
- I did not rebuild target/release/hoh.exe; freshness rests on sha256 310075fa...7158ca and mtime 02:45:40 matching the T12 record with only docs changed since.
- I did not verify the content of the A0 scaffold beyond hashes/sizes.
- I did not re-derive the editor/godot process liveness at close (pid 948) - the round is over.

## 6. 给下一批的建议

1. **不要重跑轮次**：判据与复现结论已成立，重跑只会复现同一批机制噪声。需要的是**改报告**（`T13A-1/2/3/4/5/6/7/8/9`），并在下一份真机任务书里加两条机械检查：
   - 报告里任何「0 次 / 未触发 / 逐位相同」断言，必须由脚本从**最终工件**复算，且脚本要覆盖 `extra.hoh_output_truncated` 这类字段（不是 grep 原始字节）。
   - 任何「某次 start_round_game 失败」的归因，必须给出**该次调用对应的时间戳来源**（warnings.log mtime / 轨迹时间戳），不得用 `meta.started_at` 代替。
2. **把 `:53068` 的发现写进台账**：轮内首次起游戏成功、修复重试那次起游戏失败；`developer.md:33` 的「route for the whole round」承诺在修复窗口内为假。下一批若要查 DR-70 根因，应插桩游戏进程的绑定时刻，并同时记录 `game_endpoint.json` 的存在性时间线。
3. **把 64 KiB 首次触发登记为机制读数**（Tester 读 `.hoh/deterministic/raw/interaction_evidence.json` 时被截），并决定角色读取原始证据的推荐姿势（写 scratch 再切片，提示词已这么要求）。
4. **修 `artifact_valid` 的语义**（或至少修报告）：修复尝试应重新判定，而不是 `workspace.is_dir()`；`artifact_valid` 目前无法区分「可用工程」与「模型停手的工程」。
5. **修 `usage_from_attempts` 的过滤器**：排除 `*.redacted.json`（一行），并给 planner/tester 用同一条「按 attempt 合并」的路径。
6. **环境隔离**：角色 shell 不应继承 `DSH_*`（至少 `DSH_TERM_CMD`）；并把「扫描非密钥环境值」加进 hygiene 脚本。
7. **卫生**：`out_of_tree_writes` 目前只报不治（本轮 3 个仓根 `.tmp_*.json`）；建议让 developer 的临时 args 落到 scratch，或在收尾时把越界文件登记进 `closing_state`。

