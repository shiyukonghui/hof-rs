# TASK-DR73-ACCEPTANCE — DR-73 的独立验收（全新验收子代理，无实现者上下文）

> 验收人：**独立验收子代理**（本批实现者与调度者之外的全新代理；未继承任何结论）。
> 落点：`F:\moonbit-hof-rs`。被验对象：`.spec/hof-rs/tasks/TASK-DR73.md`（任务书）、
> `.spec/hof-rs/tasks/TASK-DR73-REPORT.md`（实现者报告，**只作线索**）、
> HEAD = `85c9c44`（`4deefc8` + 报告提交），开工 HEAD `34bd31c`。
> **离线**：未启动 Godot、未触端口、未联网、未调模型端点、未跑真机轮；**未 push、未 stage**；
> **`runs/**` 零写入（含"写过再删"）**；分析脚本与备份全部在仓外
> `C:\Users\wyl\AppData\Local\Temp\dr73acc\`；**未用 `rm -rf`**；未由未展开变量构造路径。

---

## 0. 机器可读结论块（fence-aware JSON，已用 `json.loads` 亲验通过）

```json
{
  "verdict": "fail",
  "criteria": [
    {"id": "D1-wiring", "pass": true, "evidence": "coin.gd:13 body_entered.connect / :24-28 group check / :34-37 add_coin+queue_free, goal.gd:6-17 reached+win(); main.tscn has ZERO collision_layer/collision_mask/monitoring overrides (grep over the whole 288-line file returns none). Engine readings: Player collision_layer=1 collision_mask=1 grounded=true; Goal reached=false monitoring=true mask=1 shape not disabled."},
    {"id": "D2-coins-swept", "pass": true, "evidence": "I recomputed the AABB(circle) overlap of the 24x32 player box against CircleShape2D r=11 from the frozen per-frame samples: Coin1(300,290) overlapped in 24 samples (move_right window, consecutive frames), Coin2(425,290) in 21 samples (move_right_release). hud rollout: 91 occurrences of 'Coins: 0' and ZERO occurrences of any Coins: <non-zero> in the whole runs/smoke-t10 tree."},
    {"id": "D3-goal-unreachable-claim", "pass": false, "evidence": "FALSE. Ground is one StaticBody2D 6800x40 at (3400,320) => x in [0,6800], top y=300, continuous under the whole level including x=6400. Goal is 40x80 at (6400,280) => trigger when player x >= 6368. The only obstacle between the observed max x and the goal is the 32x60 Wall at 1700 whose top is 28 px above the walking surface, within the 66 px jump apex. The report's 'no landing surface past Platform3 right edge (x=3800)' and 'the level is impassable' are not supported; the player simply was never driven far enough."},
    {"id": "D4-max-x-number", "pass": false, "evidence": "The report says the whole-round observable max x was 448.666. The frozen samples' maximum is 455.999572753906 (jump window, x constant). Off by 7.33 px; the conclusion is unaffected but the cited number is wrong (the earlier T10 acceptance repeats 448.7)."},
    {"id": "D5-layer-B-excluded", "pass": true, "evidence": "The contract already observes and drives: running_game_get_node_properties returned the Coins label text and Goal reached=false on the real machine; running_game_assert_node_state was 4/4 passed=true; create/play/stop input recording moved the player 216.333 px. The new step uses only existing tool names and godot-mcp is byte-unchanged (nested HEAD fc63af77c33368c4a1bb839c95d19750554f63a3, porcelain 0 lines). Excluding (B) is sound."},
    {"id": "D6-mechanism-gap-unclaimed", "pass": true, "evidence": "Report 2.5 explicitly refuses to name the runtime mechanism behind 'swept but not collected' and lists three possibilities it cannot distinguish offline. I could not distinguish them either (no Godot allowed). Leaving it unclaimed rather than guessed is the correct behaviour."},
    {"id": "N1-no-handwriting", "pass": true, "evidence": "All 17 project files of .workspace/mario are byte-identical (sha256) to the frozen runs/smoke-t10/iter-1/candidate AND to the frozen version ed98d1b8...: project.godot, scenes/main.tscn, scripts/*.gd + *.uid + README.md. No file under .workspace/mario or runs/ has an mtime after 2026-09-30 18:23:08 (my find -newermt 2026-10-01 returns 0 for both). git diff 34bd31c..HEAD touches only src/, tests/, .spec/. Zero bytes written to the game."},
    {"id": "N2-pipeline-side-only", "pass": true, "evidence": "git diff --name-status 34bd31c..HEAD = 9 M + 5 A, all under src/ (adapter, cli_impl, main, prompts, secrets) or tests/ or .spec/. No deletion, no rename, no game file."},
    {"id": "O1-coin-discovery-real-shape", "pass": false, "evidence": "MAJOR. hud_label_path (godot.rs:4100-4121) finds the counter by requiring node['text'] to start with 'Coins:'. The real running_game_get_scene_tree payload gives Label nodes with exactly ['name','path','type'] and NO 'text'. I checked all 10 frozen scene-tree payloads in runs/smoke-t5|t6|t7|t8|t10 (scene_tree.json and play_scene_ready.json): every Label has keys name,path,type only. So on a real round coin_label is always None => the (None,_,_) branch => COIN_COUNTER_UNREADABLE and ok=false, no matter what the game does. The green test only passes because tests/evidence_battery.rs::node_tree_payload INVENTS a 'text' field on the synthetic HUD cells."},
    {"id": "O2-drive-budget", "pass": false, "evidence": "MAJOR (same family). INTERACTION_MAX_BATCHES=24 x INTERACTION_BATCH_FRAMES=60 = 1440 frames = 24 s of play = about 5280 px at the PRD's 220 px/s. The frozen goal trigger needs 6308 px from spawn (x>=6368) and about 6136 px from where the interaction window starts (after input_replay the player is near x=232). So even a flawless game on the frozen level geometry is reported WIN_NOT_DRIVEN, and the record's (player max x, goal.position) pair then LOOKS like unreachability - reinforcing the false diagnosis."},
    {"id": "O3-no-property-write", "pass": true, "evidence": "step_interaction_evidence calls only read_hud_text / read_node_property / capture_replay_frame / semantic_inject_action / semantic_sample_pairs / assert_property. assert_property uses semantic::ASSERT_NODE_STATE. tests/evidence_battery.rs:4159-4168 asserts no call name contains set_node_property. I found no setter in the step's call graph."},
    {"id": "O4-failure-modes", "pass": true, "evidence": "COIN_PICKED_UP, COIN_NOT_PICKED_UP, COIN_COUNTER_UNREADABLE, COIN_COUNTER_CHANGED_WITHOUT_A_PICKUP, COIN_ASSERTION_UNAVAILABLE, WIN_DRIVEN, WIN_NOT_DRIVEN, WIN_ASSERTION_REFUSED/UNAVAILABLE, WIN_NOT_OBSERVABLE, GOAL_FLAG_NOT_FALSE_BEFORE are all present and each is reachable from a distinct branch (godot.rs:2645-2782). I exercised several of them with my own plants."},
    {"id": "O5-record-carries-numbers", "pass": true, "evidence": "The window reads Goal position (godot.rs:2541-2543) and prints 'player max x={max_x:?}, goal.position={goal_position:?}' in the WIN_NOT_DRIVEN branch; tests/evidence_battery.rs:4217-4222 asserts both strings. So unreachability is measurable - the number is present (it is the DIAGNOSIS drawn from it that is wrong)."},
    {"id": "T1-vacuity-plant", "pass": true, "evidence": "My own plants: (a) remove the invented 'text' from the fixture's Coins cell => the green test reddens with COIN_COUNTER_UNREADABLE while the fixture still picks the coin up; (b) replace the assertion's expected value by the constant 'Coins: -1' (a vacuous assertion that always passes) => 2 tests redden, including 'the expectation is the window's own before reading'; (c) set INTERACTION_MAX_BATCHES=1 => NO test reddens (the drive budget is not pinned by anything)."},
    {"id": "P1-prompts-require", "pass": true, "evidence": "developer.md:154-179 DoD item 6 names 'a collectible picked up' and 'a reachable win condition' and points at the godot-dev skill; planner.md:32-42 forbids a gate that only covers movement and names both behaviours; prompts/mod.rs planner task item 4 says the same; godot-dev.md 3a/3b give recipes (monitoring/layer/mask/group, and a copied Area2D+Goal snippet with editor_get_node_properties commands). tests/interaction_contract.rs pins all of it with 4 executable assertions."},
    {"id": "P2-recipe-truth", "pass": false, "evidence": "godot-dev.md:140-143 tells the Developer 'A real round shipped the goal at x = 6400 with no ground past x ~ 3800, so the player's maximum x over the whole round was 448 - the flag was correct and the level was not.' The ground really spans to x=6800; the statement is false and it is now DELIVERED TEXT that will mislead every future round. The same false sentence is in the 4deefc8 commit message and in tests/interaction_contract.rs:105."},
    {"id": "P3-would-discover-in-round", "pass": false, "evidence": "The new window cannot distinguish a correct game from the smoke-t10 game: the coin half always answers COIN_COUNTER_UNREADABLE (O1), and on any level longer than ~5280 px the win half answers WIN_NOT_DRIVEN (O2). So the pipeline would keep reporting gaps for E3 no matter how good the game becomes. The batch makes the absence recordable, not the behaviour observable."},
    {"id": "C1-sidecar", "pass": true, "evidence": "Original .spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/analysis/redaction_defect.txt is 2035 bytes sha256 201ae32e970c6b396ef309aacad45e986d972a6f48fbe122a46d58b31d949466 (matches the pinned constant; mtime 2026-09-30 18:31, pre-batch). Sidecar redaction_defect.redacted.txt exists, 1994 bytes, working blob == HEAD blob 6a7b16e56535c97b385f2392f7eafec78b4c87f4. My independent scan for C:\\, node_modules, moonbit-hof-rs, wyl, AppData, HOH_ARTIFACT_DIR=F, HOH_GAME_ROUTE=F, HOH_HOH_BIN=F, <redacted>; returns 0 for every one, while the original really carries them (6x C:\\, 6x node_modules, 2x wyl, HOH_GAME_ROUTE=, HOH_HOH_BIN=, HOH_ITERATION=, HOH_MODEL_API_KEY=)."},
    {"id": "C2-process-exit-code", "pass": true, "evidence": "cli_impl.rs adds PROCESS_EXIT_CODE_FILE / RUN_DIR_ENV / process_exit_code_for / write_process_exit_code / record_process_exit_code_from_env; run() exports HOH_RUN_DIR before run_round_and_finalize; main.rs calls the recorder then returns the same code. The recorder READS BACK runs/<id>/exit_code and mirrors it (not a second computation) and writes the same <code>\\n byte shape. 4 tests in tests/round_artifacts.rs, all green in my run; my plant code -> code+1 reddens with left \"6\\n\" right \"5\\n\"."},
    {"id": "C3-cr-edge", "pass": true, "evidence": "secrets.rs:221-229 makes both \\n and \\r terminators and the scanner does not consume the terminator; two new tests pin (i) the plain-text CR: span ends exactly on the CR, exactly 1 span, output 'HOH_ARTIFACT_DIR=<redacted>\\rTAIL-INVITATION\\n', bytes_changed_outside_spans==0, and the NEXT line is still redacted; (ii) the JSON-escaped CR: the value ends and the tail stays, result still valid JSON. Planting b'\\n'|b'\\r' -> b'\\n' reddens the first with left 55 right 39."},
    {"id": "G1-tests", "pass": true, "evidence": "Per-file touch loop over the 94 tracked .rs files (no wildcard), then cargo test --offline => exit 0, 57 test binaries, 523 passed / 0 failed / 7 ignored, sum from the raw per-binary result lines. cargo test --offline -- --list = 530 test entries, 0 benchmarks."},
    {"id": "G2-no-removed-no-new-ignored", "pass": true, "evidence": "I extracted the test-function names from the source at 34bd31c and at HEAD via git show: base 514, head 530, REMOVED 0, added 16. #\\[ignore\\] attributes: base 9, head 9. 523+7=530 = --list. Consistent."},
    {"id": "G3-fmt-and-line-endings", "pass": true, "evidence": "cargo fmt --check => FMT_EXIT=0. The committed blobs of all 10 files I sampled are pure LF (CR=0), e.g. src/adapter/godot.rs 253643 B CR=0 LF=5891; tests/evidence_battery.rs 175035 B CR=0 LF=4293."},
    {"id": "G4-six-plants", "pass": true, "evidence": "I re-implemented all six plants myself and each reddened its own test with the reported message, then I restored byte-exactly (cmp against an out-of-repo backup, git hash-object equal to the blob, git status --porcelain -uall empty): CR terminator (secrets 1199 left 55 right 39); coin assertion text->visible (COIN_ASSERTION_UNAVAILABLE); DoD wording (interaction_contract red); recorder code+1 (round_artifacts left \"6\\n\" right \"5\\n\"); goal property renamed (3 evidence_battery tests red); sidecar marker shortened (left 0 right 2)."},
    {"id": "G5-stale-artifact-trap", "pass": true, "evidence": "Reproduced the shape: cargo test --test no_such_test_target => cargo exit 101 while the filtered view 'grep -E \"^test .*FAILED\"' is EMPTY with grep exit 1, and the pipeline exit is grep's, not cargo's. A filtered read of a failed build is indistinguishable from all-green. I therefore read exit codes from files, not from pipes, for every gate reading in this report."},
    {"id": "G6-runs-untouched", "pass": true, "evidence": "My own digest scheme: repo-root-relative lowercased path with forward slashes, TAB, decimal byte length, TAB, sha256 hex; entries sorted ORDINALLY; joined with \\n; sha256 of the UTF-8 blob, no trailing newline. Reproduced all five: t6 135 c144ef3219e21dd322978e41a5531d53dee270619c026585505920f9277a9c03 (the required self-check, hit), t7 115 6e4c1595...520fb7, t8 358 c347bd63...b3d3f5, t9 83 541e2d81...36ca9d, t10 232 9ba72fbd...e0963ad. File counts and mtimes match the frozen records; find runs -newermt 2026-10-01 = 0. Ordering DOES matter: ordinal sort of ['B/x','a/y','a/B'] gives B/x, a/B, a/y while casefold gives a/B, a/y, B/x."},
    {"id": "G7-forbidden-trees", "pass": true, "evidence": ".workspace/mario 17 project files byte-identical (see N1); PRD-mario.md 5375 B sha256 4c81c3a9995f0b3afdf01421a0c3be88573cceefc284ce9bafbfda141f0f5c3a; DECISIONS.md untouched by 34bd31c..HEAD; nested engine HEAD fc63af77c33368c4a1bb839c95d19750554f63a3 with porcelain 0; Cargo.toml/Cargo.lock unchanged (no new dependency); git rev-list --left-right --count origin/master...master = 0 2 (not pushed)."},
    {"id": "G8-false-green-traps", "pass": true, "evidence": "(1) git diff --stat -- definitely/not/a/real/path exits 0 with empty output, indistinguishable from 'unchanged'; the control is git ls-files godot-mcp = 6484 (real hit) vs git ls-files godot-mcp/godot = 0. (2) in cmd, git rev-parse HEAD^ printed 85c9c44 (i.e. HEAD) - the caret was eaten; in bash HEAD^ resolves and cat-file exits 128 vs 0. (3) the outer repo does not track godot-mcp/godot, runs/** or .workspace/** (git check-ignore: .gitignore:33/12/11; ls-files counts 0 for each)."},
    {"id": "H1-DST-disclosure", "pass": true, "evidence": "The seven tracked paths %DST%/red/* all match their HEAD blobs now (7/7, hash-object == rev-parse HEAD:<path>). Neither DR-73 commit touches %DST% (git show --stat | grep -c DST = 0 for both). The only commit that ever touched %DST% is the historical 51f9987. git diff --name-status 34bd31c..HEAD has no D or R entry, and git status --porcelain -uall is empty => no other tracked file was lost or altered. The restore COMMAND itself is not reproducible from the tree (process claim)."},
    {"id": "H2-unverified-list-and-wrapper", "pass": false, "evidence": "Report disclosure 5 says 'scripts/run_round.ps1 does not exist ... the wrapper itself is no longer in the repository'. FALSE: the wrapper IS tracked at .spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/scripts/run_round.ps1 (git ls-files hits it; added by 15e071f) and ROUND_EXIT=$ec is on line 14 - exactly the line T10A-4 cites. The implementer only checked the repo-root scripts/ directory. The carried item (b) remains justified by T10A-4, but the stated reason is wrong."}
  ],
  "defects": [
    {"id": "A1-coin-counter-undiscoverable", "severity": "major", "what": "The new interaction window can never find the coin counter on a real round: hud_label_path requires a 'text' member on a Label node of running_game_get_scene_tree, and the real engine sends only name/path/type (verified on 10 frozen payloads from five rounds). Every real round therefore takes COIN_COUNTER_UNREADABLE / ok=false, even a perfect game. The batch's headline objective (make E3's pickup observable in-round) is not achieved, and the whole point of the fixture patch is hidden from the tests. The fixture node_tree_payload invents the missing text field, so no test covers the real shape.", "reproduction": "Out-of-repo python: parse runs/smoke-t10/iter-1/candidate/.hoh/deterministic/raw/scene_tree.json, walk j['tree'], print sorted(label.keys()) => ['name','path','type'] for all 5 HUD labels; same for smoke-t5/t6/t7/t8 scene_tree.json and play_scene_ready.json (10 payloads, 0 with text). Then my plant: delete the \"text\": \"Coins: 0\" line of the synthetic Coins cell in tests/evidence_battery.rs::node_tree_payload and run cargo test --offline --test evidence_battery the_interaction_window_records_a_real_coin_pickup_and_its_assertion => FAILED with 'interaction: COIN_COUNTER_UNREADABLE ... F10 cannot be observed' although the same fixture says COIN counter went 0 -> 1 and WIN_DRIVEN."},
    {"id": "A2-drive-budget-cannot-reach-the-frozen-goal", "severity": "major", "what": "24 batches x 60 frames = 1440 frames = 24 s = about 5280 px of travel, but the frozen goal's trigger is 6308 px from spawn and about 6136 px from where the window starts. Even a correct game on the frozen geometry is recorded as WIN_NOT_DRIVEN, and the accompanying (player max x, goal.position) pair then reads as unreachability. Nothing pins the budget: reducing INTERACTION_MAX_BATCHES from 24 to 1 reddens no test at all.", "reproduction": "Arithmetic from the frozen numbers (220 px/s measured at 3.6667 px/frame; goal Area2D 40x80 at x=6400 so the player box (half-width 12) touches at x>=6368). Plant: set INTERACTION_MAX_BATCHES=1 in src/adapter/godot.rs:3733 and run the whole cargo test --offline --test evidence_battery => 'test result: ok. 49 passed; 0 failed' - the budget is not pinned."},
    {"id": "A3-level-impassable-claim-false", "severity": "major", "what": "Report 2.2(A-3) and the delivered godot-dev.md 3b state that the level has no ground past x~3800 and is therefore impassable, and that the goal is positionally unreachable. In fact the Ground node is a single 6800x40 RectangleShape2D centred at x=3400 covering x in [0,6800] with an enabled collision shape, i.e. continuous all the way under the goal. The true cause of 'the win was never driven' is coverage (the replay never drove far enough), not level geometry. The false sentence is also in the 4deefc8 commit message and in tests/interaction_contract.rs:105, and it is now delivered text that will mislead the next Developer into shortening a level that was already fine.", "reproduction": "Read runs/smoke-t10/iter-1/candidate/scenes/main.tscn lines 11-12, 44-48, 96-100, 240-245; confirm with the engine's own editor_get_collision_info for Ground in .hoh/deterministic/raw/node_and_collision_assertions.json (has_shape true, disabled false, layer/mask 1, shape s_ground). Ground top y=300 vs the observed player y=283.999 constant across the whole move_right window => the player walks on that ground; the only obstacle to x=6400 is the 32x60 Wall at 1700 whose top is 28 px above the surface, well inside the 66 px apex the report itself computes."},
    {"id": "A4-max-x-citation", "severity": "minor", "what": "Report 2.2(A-3) and the T10 acceptance both cite the whole-round maximum player x as 448.666. The frozen samples' maximum is 455.999572753906 (the jump window's constant x, confirmed by the engine's own assert payload actual.x). 7.33 px understated. Does not change any conclusion.", "reproduction": "Parse input_replay.json calls, take running_game_get_node_property_samples with position, compute max over the four windows => 455.999572753906; the same value appears as actual.x in the jump window's running_game_assert_node_state reply."},
    {"id": "A5-wrapper-script-claim-false", "severity": "minor", "what": "Honest-disclosure item 5 asserts scripts/run_round.ps1 does not exist and that the wrapper is no longer in the repository. It is tracked at .spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/scripts/run_round.ps1 and its line 14 is exactly the ROUND_EXIT=$ec line T10A-4 cites. This is the same class of tree claim the batch is supposed to be careful about.", "reproduction": "git ls-files | grep run_round => .spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/scripts/run_round.ps1; git log --diff-filter=A -- <path> => 15e071f; sed -n 14p of that file => \"ROUND_EXIT=$ec\"."},
    {"id": "A6-sidecar-test-marker-vacuity", "severity": "minor", "what": "Two of the six (marker, leaked) pairs in the_sidecar_carries_no_environment_value_and_no_user_name are vacuous: the loop only fires when the line contains the marker, and the sidecar contains neither 'HOH_ARTIFACT_DIR=' nor 'PATH=', so those checks can never fail. The real guarantee comes from the three global assertions (no C:\\, no node_modules, no moonbit-hof-rs), which I confirmed independently. Also report 5.1 says the original carries HOH_ARTIFACT_DIR= and a PATH= tail; the original has neither literal token (its first recorded line is truncated mid-word and the PATH-like tail follows HOH_MODEL_API_KEY=<redacted>;).", "reproduction": "python scan of the sidecar: count of 'HOH_ARTIFACT_DIR=' = 0 and 'PATH=' = 0; grep -c HOH_ARTIFACT_DIR on the original = 0."},
    {"id": "A7-citation-drift", "severity": "info", "what": "Two plant-table line citations are off: secrets.rs:222 vs the actual b'\\n' | b'\\r' arm at :223, cli_impl.rs:798 vs the actual write at :803. Report 8.2 says the pre-commit status had 13 items (9 M + 4 ??); the real change set is 14 paths (9 M + 5 A, the fifth addition being the report itself).", "reproduction": "git diff --name-status 34bd31c..HEAD (14 lines); read src/runtime/secrets.rs:223 and src/cli_impl.rs:803."}
  ],
  "risks": [
    "The interaction window mutates the game before node_and_collision_assertions runs: it holds move_right for up to 24 s of game time and can drive the level's win/lose branch (win() sets controllable=false; main.gd's _process decrements time_left). Downstream battery steps and the Tester then read a perturbed world. No test covers this ordering effect and I could not run the engine to measure it.",
    "HOH_RUN_DIR is a process-global environment variable set inside cli_impl::run; a second round in the same process would overwrite it. The report discloses this (its unverified item 4); production runs one round per process.",
    "record_process_exit_code_from_env mirrors runs/<id>/exit_code rather than the ExitCode value main.rs actually returns; this is consistent on the current paths but the recorder does not verify equality with the returned code, so a future divergence between finalize_run's file and main_entry's return value would make the third reading silently wrong.",
    "The evidence_battery fixture patches the scene tree with a 'text' field the engine never sends; every future change in this area will keep looking green. A fixture derived byte-for-byte from a frozen real payload would have caught A1.",
    "If the pipeline follows the new godot-dev.md 3b literally it will move the goal closer for the wrong reason (the belief that the ground ends at 3800), while the real limiting factor is the battery's own drive budget."
  ],
  "unverified": [
    "The runtime mechanism behind 'the player box overlaps the Area2D for 24 consecutive physics frames yet body_entered never fires' - offline, no Godot. The report leaves this unclaimed, which is correct.",
    "Whether the frozen level is passable end-to-end in the real engine (enemy collisions, the 1700 wall jump). I verified it geometrically from main.tscn, not by simulation.",
    "The exact commands the implementer ran during the %DST% incident (rm -rf of the literal name, git restore --source=HEAD). I verified only the outcome (7/7 blobs equal HEAD now, absent from both commits, no other tracked file lost).",
    "The two 'unreliable red/green' episodes in report 1.1 (fingerprint staleness on tool_vocabulary; the compile failure read through a stale filter). I reproduced the filtered-read trap in general but not those two specific events.",
    "The precise ordering/culture claims in report 8.1 about PowerShell Sort-Object diverging on t8/t10 - I reproduced the ordinal scheme only.",
    "Whether a real round with the new step would in practice stop before the win for reasons other than the budget (sampling latency, reachability of the goal read)."
  ]
}
```

---

## 1. 逐项裁定表（任务书的七项工作）

| # | 工作 | 裁定 | 关键证据（自产） |
|---|---|---|---|
| 1 | 诊断：接线 / 扫过 / 算术 / 排除 (B) / 诚实空白 | **部分不成立** | 接线与扫过**成立**；"关卡不可通"**不成立**（Ground 6800 宽，x∈[0,6800]）；(B) 排除**成立**；空白**恰当** |
| 2 | 禁止手工写游戏（零字节） | **成立** | 17 个工程文件与 `candidate` 及 `versions/ed98d1b8…` **逐字节相同**；`find -newermt 2026-10-01` = 0；改动全在 `src/ tests/ .spec/` |
| 3 | 观测而非伪造 + 断言不空转 | **不成立（major）** | `hud_label_path` 要求 `Label.text`，而**10 份真实场景树载荷**的 Label 只有 `name/path/type` ⇒ 真机恒 `COIN_COUNTER_UNREADABLE` |
| 4 | 提示词 / 技能 / 判据 | **部分成立** | 要求与配方齐备且被 4 条测试钉住；但配方含**假陈述**（"x≈3800 之后无地面"），且观测窗**分辨不了对错** |
| 5 | 三条携带项 | **成立** | sidecar 原件 2035B/`201ae32e…` 未动、sidecar 零泄漏；`process_exit_code` 镜像落盘；CR 两侧各一条钉 |
| 6 | `%DST%` 披露 | **成立** | 7/7 `hash-object == HEAD:<path>`；两个提交 0 触碰；`34bd31c..HEAD` 无 D/R |
| 7 | 门 / 植入 / 守卫 / 陷阱 / 未验证清单 / 包装脚本 | **门与植入成立；包装脚本断言不成立** | `523/0/7`、`--list 530`、`fmt 0`、6 植入亲复现；`run_round.ps1` **存在于仓内** |

---

## 2. 我自产的植入与反例（全部逐字节回退）

方法与实现者一致但我**自己重做**：仓外备份 `…/dr73acc/bak/`，`edit` 最小植入，跑**对应**测试取红，
`cp` 回退后 `cmp` + `git hash-object` + `git status --porcelain -uall` 三重核对。

### 2.1 复现实现者声明的 6 处植入

| # | 我的植入 | 落点 | 红输出（逐字） | 回退 |
|---|---|---|---|---|
| 1 | `b'\n' \| b'\r'` → `b'\n'` | `src/runtime/secrets.rs:223` | `panicked at src\runtime\secrets.rs:1199:9: the span must end on the carriage return, not past it; left: 55 right: 39` | `cmp` OK, blob `30a34483…` |
| 2 | 金币断言属性 `"text"` → `"visible"` | `src/adapter/godot.rs:2659` | `FAILED … COIN_ASSERTION_UNAVAILABLE (the game process could not answer text:neq "Coins: 0")` | `cmp` OK, blob `49e1fe87…` |
| 3 | DoD `"a collectible picked up"` → `"an interactive object"` | `src/prompts/developer.md:158` | `the_developer_definition_of_done_requires_the_two_missing_behaviours ... FAILED` | `cmp` OK, blob `59e5d451…` |
| 4 | 记录器 `code` → `code + 1` | `src/cli_impl.rs:803` | `left: "6\n" right: "5\n"` | `cmp` OK, blob `6c153c2f…` |
| 5 | `goal_after` 属性 → `"reached_after_the_drive"` | `src/adapter/godot.rs:2637` | 3 条 `evidence_battery` 测试红（`WIN_NOT_OBSERVABLE (goal.reached=None after the drive)`） | `cmp` OK, blob `49e1fe87…` |
| 6 | sidecar 标记文本改短（生成器） | `tests/round_artifacts_sidecar.rs:68` | `left: 0 right: 2 — every recorded occurrence must be replaced by the marker, not copied` | `cmp` OK（含 sidecar 与原件三种文件全部回退） |

⇒ **6/6 亲复现**，且每次 `git status --porcelain -uall` 归零、`hash-object` 与 HEAD blob 相同。
**注意**：植入 6 会把 sidecar 写坏（`build_sidecar` 先写后断言），我因此**先备份 sidecar 与原件**，
回退后 `cmp` 三者全部一致，`redaction_defect.redacted.txt` 的 blob 仍是 `6a7b16e5…`（= HEAD）。

### 2.2 我另外加的三处（任务书要求"让断言空转看是否变红"）

| # | 植入 | 目的 | 结果 |
|---|---|---|---|
| P7 | 删掉 fixture 里合成 Coins 单元格的 `"text": "Coins: 0"`（= 让 fixture 与**真机**同形） | 证明 fixture 多给的那个字段**承重** | **红**：`COIN_COUNTER_UNREADABLE (no Label under HUD whose text starts with Coins:)` —— 而**同一** fixture 明说计数从 `Coins: 0 → Coins: 1`、`WIN_DRIVEN`。**这是本批核心缺陷的可执行证明** |
| P8 | 断言期望值由"窗口自己的前读"改成常量 `"Coins: -1"`（= 断言空转，永远通过） | 断言本身是否被钉 | **红**：`the expectation is the window's own before reading` + `a_project_that_never_picks_a_coin_up…` 共 2 条 |
| P9 | `INTERACTION_MAX_BATCHES` 24 → 1 | 驱动预算是否被任何测试钉住 | **不红**：`49 passed; 0 failed`。⇒ 预算是**未受钉的任意常量**，缩到 1 秒也没有测试会抗议 |

### 2.3 三个假绿陷阱（实测）

1. `git diff --stat -- definitely/not/a/real/path` → **stdout+stderr 皆空、exit 0**，与"无变化"不可区分；
   对照必须用真命中：`git ls-files godot-mcp` = **6484**（真）/ `git ls-files godot-mcp/godot` = **0**（空判）。
2. `cmd` 下 `^` 被吃掉：`git rev-parse HEAD^` 打出 `85c9c44…`（= HEAD，而 HEAD^ 应为 `4deefc8`）；
   bash 下 `git cat-file -e HEAD:definitely/not/here` 退 128、真路径退 0 ⇒ 有证据力的只有 bash。
3. 外层仓不跟踪 `godot-mcp/godot`、`runs/**`、`.workspace/**`（`.gitignore:33/12/11`，三处 `ls-files` 皆 0）
   ⇒ 这三处的"未变"只能靠目录摘要 / 嵌套仓 / mtime。

### 2.4 陈旧产物陷阱（我复现的形状）

```
cargo test --offline --test no_such_test_target        → cargo_exit=101
cargo test --offline --test no_such_test_target | grep -E "^test .*FAILED"
                                                       → 空输出, pipeline_exit=1（grep 的退出码）
```
⇒ **编译/目标错误经过滤后与"全绿"不可区分**。本报告所有门读数一律 `> file 2>&1; echo $?` 后读文件。

---

## 3. 对每一项的独立判断（任务书的 7 问）

### 3.1 诊断（工作 1）
- **接线**：`coin.gd:13/24-28/34-37`、`goal.gd:6-17`、`player.gd:31` 与报告所述逐行一致；`main.tscn` 全 288 行
  **没有任何** `collision_layer`/`collision_mask`/`monitoring` 覆盖。引擎自己的读数：`Player collision_layer=1 mask=1`、
  `Goal reached=false monitoring=true mask=1`、Ground/Player/Goal 的 `CollisionShape2D` 都 `has_shape=true disabled=false`。
  ⇒ **生产层的可观测地址与常见接线都是齐的**，这正是 (A) 的判据。
- **扫过**：我按 AABB–圆距离公式重算，`Coin1` 有 **24 帧**重叠、`Coin2` 有 **21 帧**重叠（不是临界一帧）。
  全轮 `Coins: 0` 出现 **91 次**，`Coins: <非0>` **0 次**，`Goal.reached` 的**引擎读数只有 false**。
  ⇒ **"扫过而不触发"是真实的产品缺陷**，层 (A) 在金币这一半**成立**。
- **算术**：`135 px/跳` 的公式本身正确（`220×2×430/1400 = 135.1`）。但**前提错了**：
  `Ground` 是**一块** `6800×40 @ (3400,320)` 的 `RectangleShape2D` ⇒ **x∈[0,6800] 连续**，
  顶面 y=300，而全轮逐帧 y 恒为 283.999（= 站在该地面上）。`Goal` 是 `40×80 @ (6400,280)`，
  玩家半宽 12 ⇒ **x≥6368 即触发**。从 x=456 到 6368 之间唯一的实体障碍是 `Wall 32×60 @ (1700,302)`，
  其顶面比地面高 **28 px**，远在报告自己算出的 **66 px 顶点**之内，可跳；两枚敌人是伤害而非墙。
  ⇒ **"没有任何落脚面 / 关卡不可通过 / 终点位置不可达"不成立**。真因是**回放从未驱动那么远**
  （四个窗口各 ≤60 帧 ≈ 4 s ≈ 最多 900 px）。**"胜利从未被驱动"是覆盖问题（C），不是关卡缺陷（A）。**
- **(B) 排除**：**成立**。契约在真机上**既能观测**（`running_game_get_node_properties` 读到 `Coins: 0` 与
  `Goal.reached=false`；`assert_node_state` 4/4 `passed=true`）**也能驱动**（录制回放把玩家推动 216.333 px）。
  新增步骤只用契约内已有工具名，`godot-mcp/**` 零改动。**但**：契约的
  `running_game_get_scene_tree` **不携带 Label 文本**，所以"用场景树找计数格"这条**harness 用法**是错的（见 A1），
  这是**实现层的用法缺陷**，不是契约能力缺失，故不影响 (B) 的排除。
- **诚实空白**：`§2.5` 拒绝指认"扫过不触发"的运行时机制，列出三种离线不可分的可能。**我同样无法区分**
  （不许启 Godot），**把它留作未声明而非猜测，是恰当的**。

### 3.2 禁止手工写游戏（工作 2，头条）
- `.workspace/mario` 的 **17 个工程文件**（`project.godot`、`scenes/main.tscn`、7 个 `.gd` 及 `.uid`、README）
  与**冻结的 `runs/smoke-t10/iter-1/candidate`** 与**冻结版本 `versions/ed98d1b8…`** 三方 **sha256 全部相同**。
- `.workspace/mario` 与 `runs/**` 下**没有任何文件** mtime 晚于 `2026-09-30 18:23:08`（即 t10 收轮时刻）；
  本批开工是 2026-10-01。`find … -newermt '2026-10-01 00:00'` 两处皆 **0**。
- `git diff --name-status 34bd31c..HEAD` = **9 M + 5 A**，全在 `src/`、`tests/`、`.spec/`；**无删除、无重命名、无游戏文件**。
⇒ **零字节写入，全部改动在流水线侧。这一条成立。**

### 3.3 观测而非伪造（工作 3）—— 本批的**核心失败**
新步骤确实只用既有工具、确实不写属性、确实产出 before/after PNG、确实用引擎自己的
`running_game_assert_node_state`。**但它找不到金币计数格**：

> `hud_label_path`（`src/adapter/godot.rs:4100-4121`）要求 `Label` 节点的 **`text`** 以 `"Coins:"` 开头。
> 而真实的 `running_game_get_scene_tree` 给 HUD 下的 Label 只有 **`name` / `path` / `type`**。

我把 `runs/smoke-t5|t6|t7|t8|t10` 的 `scene_tree.json` 与 `play_scene_ready.json` **共 10 份真实载荷**逐份 walk：
**每一份、每一个 Label 的键集合都恰是 `['name','path','type']`，`text` 命中数 = 0。**
⇒ 真机上 `coin_label` 恒为 `None` ⇒ 恒走 `(None,_,_)` 分支 ⇒
**`COIN_COUNTER_UNREADABLE` + `ok=false`，与游戏对错无关**。

而 `tests/evidence_battery.rs::node_tree_payload`（`:107-169`）在合成 HUD 单元格时**自己塞进了 `text` 字段**
（注意 `scene_tree.json` 里那个 `"type": "text"` 是 JSON-RPC 内容的包裹，不是 Label 文本）。
我的 P7 植入（删掉那个字段、其余不动）⇒ 绿测立刻变红并打出 `COIN_COUNTER_UNREADABLE`，
**同一 fixture 却同时说金币计数 0→1、且 `WIN_DRIVEN`**。这是 fixture 比现实更宽而导致的假绿。

研判词、`ok=false` 语义、`player max x` + `goal.position` 的记录形态**都做到了**（工作 3 的其余子项成立），
但**"让这两件事在轮内可观测"这一目标没有达成**：它让"缺失"可记录，却**没有让"行为"可观测**。

### 3.4 驱动预算（附带但同族）
`INTERACTION_MAX_BATCHES=24` × `INTERACTION_BATCH_FRAMES=60` = **1440 帧 = 24 s ≈ 5280 px**
（实测 3.6667 px/帧 ⇒ 220 px/s，与冻结轨迹一致）。冻结关卡的触发点在**离出生点 6308 px**、
**离交互窗起点（`input_replay` 收在 x≈232）约 6136 px** 处 ⇒ **即使游戏完美也报 `WIN_NOT_DRIVEN`**，
而记录里的 `(player max x, goal.position)` 又会**看起来像"不可达"**，反过来强化 A3 的错误诊断。
我的 P9 证明**这个预算没有任何测试钉住**（24→1 全绿）。

### 3.5 提示词与规则（工作 4）
- **要求齐备**：`developer.md:154-179` 完成定义第 6 条点名 `a collectible picked up` 与 `a reachable win condition`，
  并要求"计数移动"这一可观测；`planner.md:32-42` 明确"只覆盖移动与跳跃的闸门不构成成功"；
  `prompts/mod.rs` 的 planner 任务书第 4 条同口径；`godot-dev.md` 3a 给出 `monitoring`/`collision_layer`/`collision_mask`/
  `add_to_group`/`is_in_group` 四条检查与可抄代码、3b 给出 Goal 代码与 `editor_get_node_properties` 命令。
  `tests/interaction_contract.rs` 的 4 条断言把上述文本钉住（我逐条核对，实际文本满足）。
- **但配方含假陈述**：`godot-dev.md:140-143` 写死 "no ground past x ≈ 3800 … the level was not [correct]"。
  这条**会被交付给下一轮的 Developer**，而事实是地面连续到 6800。同一句还进了提交信息与
  `tests/interaction_contract.rs:105` 的注释。
- **能否让流水线"轮内发现"**：**不能可靠发现"对"**。因为 A1 的假阴性使金币半边**永远**报
  `COIN_COUNTER_UNREADABLE`，A2 使长关卡必然报 `WIN_NOT_DRIVEN`。它能让 Tester 把 F10/F13 如实记为
  gap（比 t10 的"零证据"好），但**无论把游戏修得多好，E3 都不会 met**——这正是本批要修的目标本身。

### 3.6 三条携带项（工作 5）
- **(a) sidecar**：原件 2035 B、`sha256=201ae32e970c6b396ef309aacad45e986d972a6f48fbe122a46d58b31d949466`
  （与测试里的钉值一致），mtime `2026-09-30 18:31`（本批之前）；sidecar 1994 B，工作树 blob == HEAD blob
  `6a7b16e5…`。我用自己的脚本扫 `C:\`、`node_modules`、`moonbit-hof-rs`、`wyl`、`AppData`、
  `HOH_ARTIFACT_DIR=F`、`HOH_GAME_ROUTE=F`、`HOH_HOH_BIN=F`、`target\debug`、`<redacted>;`、`HOH_MODEL_API_KEY=sk`
  **全部 0 命中**；而原件确实带着这些值（6×`C:\`、6×`node_modules`、2×`wyl`、`HOH_GAME_ROUTE=`、`HOH_HOH_BIN=`、
  `HOH_ITERATION=`、`HOH_MODEL_API_KEY=`）⇒ 断言不是空转。**成立**（两处 marker 检查空转见 A6）。
- **(b) 进程退出码**：设计是**镜像**（读回 `runs/<id>/exit_code` 原样落盘），不是第二次计算；写成同样的
  `<code>\n`。`run` 在**任何角色之前** `set_var(HOH_RUN_DIR)`；`main.rs` 记录后返回同一个 `code`；
  `finalize_run` 正是那个单点 `run_exit_code_for(summary)`。4 条测试我全跑绿（含"不是轮次不写""空值""无裁决不写"
  三个反例，且用非 0 值 `5`）。我的 `code+1` 植入红成 `left "6\n" right "5\n"`。**成立**。
- **(c) `\r` 边界**：`is_value_terminator` 把 `\n` 与 `\r` 都当终结符且**不消费**（`assignment_value_end`），
  于是现实形态是"CR 之后同一物理行的余部存活"。两条测试分别钉（i）纯文本 CR：span 恰止于 CR、span=1、
  输出逐字 `HOH_ARTIFACT_DIR=<redacted>\rTAIL-INVITATION\n`、`bytes_changed_outside_spans==0`、
  **且 CR 的下一行仍被脱敏**；（ii）JSON 内的 `\`+`r` 是**转义族**：值尾后内容存活且结果仍是合法 JSON。
  两形态不混。**成立**。

### 3.7 `%DST%` 披露（工作 6）
- 7 个路径 **全部** `git hash-object == git rev-parse HEAD:<path>`（`7127c746…`、`48179138…`、`a2829e0b…`、
  `7b4b900c…`、`cd87542a…`、`0c59d727…`、`52db4d83…`）。
- 两个 DR-73 提交的 `--stat` 里 `%DST%` 命中数 **0 / 0**；历史上唯一触碰 `%DST%` 的提交是旧的 `51f9987`。
- `git diff --name-status 34bd31c..HEAD` **无 D、无 R**；`git status --porcelain -uall` 空
  ⇒ **没有其它已跟踪文件丢失或被改**。
- 该目录 mtime `2026-10-01 16:03`，与披露的时刻相符。
⇒ **结果层面 7/7 可核**；**"rm -rf '%DST%' 然后 git restore"这一过程本身无法从树里复现**（记为未验证）。

### 3.8 门、植入、守卫、陷阱、未验证清单（工作 7）
- `cargo fmt --check` → **FMT_EXIT=0**。
- 逐文件循环 touch **94** 个 `git ls-files '*.rs'`（无通配符 touch）后 `cargo test --offline` →
  **exit 0**、**57 个 test binary**、逐 binary 求和 **523 passed / 0 failed / 7 ignored**。
- `cargo test --offline -- --list` → **530** 条测试、0 benchmark；523+7=530 自洽。
- 用 `git show` 在 `34bd31c` 与 `HEAD` 上各自解析测试函数名：**514 → 530，REMOVED 0，新增 16**；
  `#[ignore]` 属性 **9 → 9**（ignored 不增）。
- 提交进仓的 blob 抽样 10 个文件**全部纯 LF（CR=0）**，与报告口径一致。
- 6 处植入亲复现（§2.1）；三个假绿陷阱亲复现（§2.3）；陈旧产物陷阱复现（§2.4）。
- `runs/smoke-t6..t10` 五条摘要我自己按 §G6 口径重算，**与报告逐字相同**，`smoke-t6` 命中 `c144ef32…7a9c03` 自证。
- `.workspace/mario` 17 文件逐字节同、`PRD-mario.md` sha `4c81c3a9…`、`DECISIONS.md` 未被两个提交触碰、
  嵌套引擎 `fc63af77…` + porcelain 0、`Cargo.toml`/`Cargo.lock` 未变（无新依赖）、
  `origin/master...master = 0 2`（未 push）。
- **未验证清单的裁断**：报告 §11 的"实测" 8 条我逐条复现，**全部成立**；"推断" 4 条我认同其**标注为推断**的
  克制（其中第 1 条尤其恰当）；"未闭合" 5 条我认同。**唯一被推翻的是 §10 披露第 5 条**（包装脚本不存在）——
  见 A5。
- **包装脚本裁断**：T10A-4 所引 `scripts/run_round.ps1:14` 的脚本**存在于仓内**
  （`.spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/scripts/run_round.ps1`，`15e071f` 加入，第 14 行正是
  `"ROUND_EXIT=$ec"`）。实现者只查了仓根 `scripts/`。**该断言为假**；但携带项 (b) 的**必要性仍由 T10A-4 的
  实质（该行从未被冻结进轮次工件）支撑**，故不推翻 (b) 本身。

---

## 4. 未验证项与理由

见结论块 `unverified`。要点：
1. **"扫过不触发"的运行时机制** —— 离线、且本批不许启 Godot；报告不指认，我也不指认。
2. **冻结关卡在真机上是否全程可通** —— 我按 `main.tscn` 的几何与碰撞形状推演（结论：可通），
   **未跑物理**。但"不可通"这一肯定断言同样没有真机证据，且被"地面连续到 6800"直接反驳。
3. **`%DST%` 事件的命令序列** —— 只验证了结果与两个提交的洁净。
4. **报告 §1.1 的两次"不可信红/绿"** —— 我只复现了"过滤读法"这一**形状**，没复现那两次具体事件。
5. **文化排序 vs 序数排序** —— 我只复现了序数口径并证明两者确实分叉；报告关于 PowerShell 分叉的说法未独立复现。
6. **新步骤在任何真机轮上的实际时序** —— 无真机。

## 5. 我没有检查的

- 未启动 Godot / 未跑任何真机轮（硬约束）；因此**不声称 E3 是否 met**（本批亦不声称）。
- 未审 `godot-mcp/**` 内部实现（只验其未改）。
- 未逐条重审 `input_replay` 既有 4 条位置断言的代码（只复核其冻结回包 4/4 `passed=true`）。
- 未核 `tests/fixtures/**` 全部夹具与真实载荷的一致性（我只查了 `node_tree` 这一族，正是它出问题）。
- 未做提交信息语言/编号的逐条审读（只确认两条都含 `(DR-73)` 且为英文）。

## 6. 给下一批的建议（按优先级）

1. **先修观测通道**：`hud_label_path` 不能用场景树的 `text`。改为**按节点名/路径在 HUD 下定位**候选
   `Label`（`name`/`path` 是真实存在的），再用 `running_game_get_node_properties{properties:["text"]}`
   **逐个读**并选取以 `Coins:` 开头者；或者由 PRD 约定固定路径 `HUD/Coins`。
   **必须同时把 fixture 换成真实场景树载荷**（`tests/fixtures` 里那份 `node_tree.json` 就是真形态），
   并加一条"真实形态载荷也能被找到"的先红测试——否则下一次仍会假绿。
2. **让驱动预算与关卡长度挂钩**：预算是 harness 侧的常量，**要么**把上限提到足以覆盖规格允许的关卡长度
   （并在交付文本里写出这个上限，让 Developer 知道"可被观测"的边界），**要么**给窗口一个"先传送到
   目标附近再驱动"的契约内手段（`running_game_move_player_to_target` 需要导航数据，属 TASK-15x 议题）。
   至少要**加一条测试钉住预算的语义**（例如"预算 × 每帧位移 ≥ 规格允许的最大关卡长度"）。
3. **撤回并更正 A3 的假陈述**：`godot-dev.md` 3b、`4deefc8` 提交信息、`tests/interaction_contract.rs:105`
   的注释都要改成事实口径："地面连续到 x=6800，目的是让玩家**按住 move_right 走得到**；
   上一轮的失败是**回放驱动距离不足**，不是关卡不通"。**不要**让下一轮因为一条假陈述去缩短本来没问题的关卡。
4. **把"上一轮为什么没驱动到"写成度量**：新窗口应记录 `start x`、`batches used`、`max x`、`goal.position`
   与**剩余预算**，并把 `WIN_NOT_DRIVEN` 再细分（`WIN_UNREACHED_WITHIN_BUDGET` vs
   `WIN_UNREACHABLE_GEOMETRICALLY`），否则两种完全不同的病因会共用同一个词。
5. **补强 sidecar 测试**：把"marker/leaked"表改成"断言原件 occurrence 数 == sidecar 标记数"这种
   **不依赖 marker 是否出现**的形式（现在两条是空转）；并修正报告 5.1 对原件内容的描述
   （原件没有 `HOH_ARTIFACT_DIR=` 与 `PATH=` 这两个字面量）。
6. **更正披露第 5 条**：包装脚本在 `TASK-SMOKE-T10-evidence/scripts/run_round.ps1`；
   把"脚本已不在仓里"改成"该行未随 `round/console.txt` 冻结入库"。
7. 若要继续保留 `player max x` 的叙述，把数字更正为 **455.9996**（冻结样本真实最大值）。

---

## 7. 机器可读块的合法性检查（我自己做的，按 D279 的机械规则）

本报告**只有一个 `json` 围栏块**（§0）。我用"栅栏感知"的方式先按
`^\s*```(\w*)\s*$` 切分，取出标记为 `json` 的块，`json.loads` 解析：

```
json-fenced blocks = 1 ; json.loads failures = 0
keys = criteria, defects, risks, unverified, verdict
verdict = fail ; criteria = 30 ; defects = 7 ; risks = 5 ; unverified = 6
```

（检查脚本在仓外 `C:\Users\wyl\AppData\Local\Temp\dr73acc\fencecheck.py`；**本报告写完后不再修改**。）

## 8. 结论

**`verdict = fail`**（3 major + 3 minor + 1 info）。

- **做对的部分要认**：禁止手工写游戏**严格遵守**（工程树零字节变化，逐字节可证）；
  三条携带项**都成立**；门的读数、6 处植入、三条假绿陷阱、五条真机基线摘要**全部可复现**；
  `%DST%` 误删事件**结果层面 7/7 可核**；对运行时机制的空白**克制且恰当**。
- **不成立的部分是致命的**：本批的**头条目标**（让金币被拾取与胜利被驱动**在轮内可观测**）**没有达成**——
  新窗口在真机上**永远找不到金币计数格**（fixture 多塞了一个真机没有的 `text` 字段而掩盖了它），
  且其驱动预算**不足以走到冻结关卡的终点**；与此同时，它**把一个错误的关卡诊断写进了交付文本**。
  按"流水线自己能产出正确游戏"这一目标衡量，**这一批把可观测性从"看不见"变成了"看错"**。
