{
 "verdict": "fail",
 "task": "independent acceptance of the bevy round-5 cost batch: the context fold and its measured reduction, the repeated-action tripwire's new semantics, defects RA-1 and RA-2/3/4/6/7/8/9, --resume, the cfg!(windows) test defect, the tree gate, and the hard constraints",
 "revision_measured": "branch bevy-core, HEAD a1f51f1 plus the batch's uncommitted worktree: 36 modified tracked paths, 2 deletions (the two Godot skill files) and 4 untracked additions (COST-REPORT.md, src/harness/compact.rs, tests/context_compaction.rs, tests/resume_round.rs); the worktree was hashed before and after and is byte-identical (F:/hof-acc5-logs/freeze1.txt = freeze2.txt, sha256 20a40be343166fc73b3a3535fef2b476c5ec9ebbc967186250fb74efccba9e7b)",
 "measured_at": "2026-10-05, offline; no engine, no game, no network, no model call; no round run; nothing written under runs/**",
 "environment": "helper scripts and logs under F:/hof-acc5-work and F:/hof-acc5-logs; build directory F:/hof-acc5-target (my own); the only tracked-tree write is this file; nothing staged, committed or pushed",
 "briefing_correction": "the briefing says the implementer wrote nothing; in fact .spec/bevy/COST-REPORT.md (28,571 bytes, untracked) was written at 2026-10-05 15:11:35, during the dispatch of this acceptance. The report was treated as an untrusted claim source and every claim below was checked against the tree and the raw evidence.",
 "cost_conclusion": "the reduction is real and independently reproduced (recorded Developer prompt tokens 20,447,131 -> projected 5,220,254, i.e. 74.5%); the 1,500,000-tokens-per-Developer-call target is NOT met: iter-2 still projects to 2,681,282 and iter-3 to 1,663,325",
 "criteria": [
  {
   "id": "I1a-context-growth-reduction-measured",
   "pass": true,
   "evidence": "I re-implemented src/harness/compact.rs's fold independently in Python (F:/hof-acc5-work/measure.py) and reproduced the batch's numbers exactly: projected prompt tokens 875,647 / 2,681,282 / 1,663,325 against recorded 2,544,563 / 12,765,478 / 5,137,090, and the published tail curve for iter-2 byte for byte (7,339,794 at tail 0 ... 15,807,809 at tail 32). The repository's own test prints the same integers (F:/hof-acc5-logs/ctx.out); its least-squares fit is slope 0.255366, worst residual 1,347 tokens, total reproduction error <0.01%. Method: per recorded call, the message prefix is reconstructed from runs/round4/iter-*/traj/developer.attempt1.json, wire-sized with mini's own four-field subset, fitted against the provider's recorded usage.prompt_tokens, folded with the repository's own compact_history, and converted with the fitted ratio. Reduction of recorded prompt tokens: 74.47%."
  },
  {
   "id": "I1b-cost-target-met",
   "pass": false,
   "evidence": "The target on record is below 1,500,000 tokens per Developer call. Projected per-call prompt tokens: iter-1 875,647 (passes), iter-2 2,681,282 (1.79x the target), iter-3 1,663,325 (1.11x). The three-call projected total is 5,220,254 against 20,940,837 recorded (prompt+completion) or 20,447,131 prompt-only. The batch's own report and D300 state that the target is not reached; the only failed criterion of the previous acceptance is therefore still failed."
  },
  {
   "id": "I2-tripwire-semantics",
   "pass": true,
   "evidence": "guard.rs: record_repeat keeps a per-action RepeatRun{digest,repeats}; a sha256-identical result extends the run, any changed result starts a new one at 1, and a counted artifact write clears the map. My own projection from the recorded trajectories (repo test with --nocapture, F:/hof-acc5-logs/rep.out): the old rule's window maxima were 16 / 15 / 17 for cargo build --offline (the counts that aborted all three round-4 calls); the identical-result maxima are 1 / 1 / 2, so the new rule aborts none of them; round 2's recorded grind (window max 22) is also no longer identical-result repetition (max 2). Pinned by two new guard tests (a_repeated_action_whose_result_changes_is_not_unproductive_repetition, a_repeated_action_whose_result_stops_changing_is_still_aborted) and by tests/repeated_action.rs."
  },
  {
   "id": "I3-RA1-ledger-ordering",
   "pass": false,
   "evidence": "The code is right: launch.rs spawns at :443 and appends the ledger at :465, the entry's note, append_ledger/ledger_entry/reap_ledger docs and the call-site comment all say 'immediately after the spawn', the nonce is generated at :368 before the spawn, and a new test spawns a real child and asserts the wording. The claim is NOT fully corrected: .spec/bevy/ROUND-4-REPORT-COMPLETE.md:73 still reads 'written by the harness before the spawn' and :131 still reads 'which the harness wrote BEFORE the spawn', while COST-REPORT.md's RA-1 disposition says that file now says otherwise; .spec/bevy/ROUND-3-REPORT.md:140 carries the same false claim. The file's only change is the RA-2 frame line (git diff of that path is one hunk)."
  },
  {
   "id": "I4-RA6-old-engine-prompts",
   "pass": true,
   "evidence": "src/prompts/skills/godot-dev.md and godot-testing.md are deleted from the worktree and from prompts::skills() (src/prompts/mod.rs now returns the two Bevy books only); the compiled F:/hof-acc5-target/debug/hoh.exe contains 0 occurrences of 'godot-dev.md' and 'godot-testing.md'. The prompt-discipline tests were re-pointed rather than dropped: tests/developer_contract.rs asserts >=7 recipes (was >=6), delivered-form needles for the Bevy path, and that no previous-engine needle is present; tests/prompt_shell_contract.rs drives a real WriteGuardEnvironment to prove the scratch recipe lands under .hoh/scratch; tests/delivered_materials.rs keeps the audience rules and re-points the Tester recipe at bevy_player_transform/bevy_grounded/tools call. One assertion (the skill must name editor_play_scene) was dropped with a stated reason and stays pinned on developer.md."
  },
  {
   "id": "I4b-no-previous-engine-prompt-shipped",
   "pass": true,
   "evidence": "include_str! of the two Godot books is gone; the gate compiles and passes, so nothing references them; binary scan finds 0 occurrences of their file names. Old-engine tool *names* survive in production code (EXAMPLE_PREFERENCE, src/tools/index.rs:120-131) and in #[cfg(test)] code, but they are never delivered: a Bevy round's tools never match those names. Recorded as defect AC-11 against the report's 'declared, not fixed' list."
  },
  {
   "id": "I5-DECISIONS-append-only",
   "pass": true,
   "evidence": "md5 of the first 11,268 lines of DECISIONS.md = 04b816fd088f808b1d70cd19cc7158be = md5 of git show HEAD:DECISIONS.md; the file grew from 11,268 to 11,414 lines; git diff shows three appended entries (D298, D299, D300) and a context hunk header at 11266, i.e. nothing before line 11268 changed and nothing was reordered."
  },
  {
   "id": "I5b-DECISIONS-accuracy",
   "pass": false,
   "evidence": "D298 (twice) and D299 (once) cite a 'D301' that does not exist; the batch's entry is D300 (grep 'D301' finds exactly three references and no '## D301' heading). D298's cost formula (prompt tokens ~= 4187 + 0.28 x cumulative wire bytes) and its 'system prompt ~5% of the final prompt' do not match this batch's own measured fit (-38.28 + 0.2554 x bytes; 14,814/161,566 = 9.2%). The substantive content of D298/D299 matches the code and the earlier reports."
  },
  {
   "id": "I6-RA2-frame-citation",
   "pass": true,
   "evidence": "runs/bevy-round4/calls/0008-bevy_grounded.json has result = {frame: 495, grounded: true}; the string '477' does not occur in the file or in any of the 57 call files (grep -l). The corrected proving_reading names the file and the frame."
  },
  {
   "id": "I6-RA3-per-pass-snapshot-semantics",
   "pass": true,
   "evidence": "RoundStopReport gained ledger_lines_at_sweep (project.rs:538, serialised) and sweep_covers_ledger_line(line) = line > 0 && line <= ledger_lines_at_sweep (project.rs:562); reap_round_processes counts the ledger's non-empty lines before sweeping (mod.rs:507-518). Pinned by the sweep test, which appends a later ledger line and asserts the earlier sweep does not cover it. The recorded snapshot files under runs/** were not rewritten (my freeze manifest covers only the worktree; nothing under runs/** was written by me)."
  },
  {
   "id": "I6-RA4-identity-verified-discriminates",
   "pass": true,
   "evidence": "identity_fields now returns a struct whose verified is the conjunction of (1) non-empty nonce, (2) answered_nonce == nonce, (3) listening_pid == spawned_pid; launch.json carries the new answered_nonce field (launch.rs:512, :525, mod.rs:956); verified_game_endpoint no longer hard-codes Some(true) (mod.rs:574-590). It can now be false for a real launch: a different or absent OS listener reading makes it false (tests pin both). Caveat filed as AC-4: terms (1) and (2) are invariants of every launch that returns, because readiness only sets answered_nonce on the matching arm (launch.rs:502-529), so the operative discrimination is the OS TCP table alone."
  },
  {
   "id": "I6-RA7-round-3-4-decision-entries",
   "pass": true,
   "evidence": "RA-7 (DECISIONS.md has no round-3/round-4 entry) is closed in substance: D299 is exactly the rounds 3-4 entry and D300 covers this batch. But the disposition in COST-REPORT says RA-7 'could not be located in this batch's copy of ACCEPTANCE-ROUNDS.md', which is false: RA-7 is at .spec/bevy/ACCEPTANCE-ROUNDS.md:137 (filed as AC-5)."
  },
  {
   "id": "I6-RA8-definitional-steps",
   "pass": true,
   "evidence": "Observation gained definitional/definitional_note ([serde(default)]); e3_grounded_payload and e3_win_position set them with their reasons (battery.rs); battery_records appends '[definitional: <reason>]' to the round's own observation text, so the record itself says which steps are existence checks rather than behavioural proofs; pinned by the_definitional_battery_steps_say_so_in_the_rounds_record with a non-definitional control (e3_coin_counter)."
  },
  {
   "id": "I6-RA9-parse-listener-pid",
   "pass": true,
   "evidence": "The candidate.get_or_insert(pid) fallback is gone (engine.rs:187-221); a row whose state is not LISTEN* is not returned, and an unrecognised (localised) state returns None. Tests cover ESTABLISHED, TIME_WAIT, a localised state word and a LISTEN row that is not first. Trade-off recorded as a risk: answerability of the OS reading now depends on the state word being recognisable."
  },
  {
   "id": "I7-resume-implemented-with-stated-scope",
   "pass": false,
   "evidence": "plan_resume (run_loop.rs:107) is pure arithmetic over iter-<n>/result.json and is pinned by five tests plus the RESUMED_FROM warning constant (all green, F:/hof-acc5-logs/resume.out); the CLI refuses a missing run directory and --fresh-workspace/--reset-workspace (cli_impl.rs), and a skipped iteration's usage/gate/version are carried into the summary. But the resume path is defective: quarantine_previous_evidence runs unconditionally at run_loop.rs:914 (before the resume branch at :934), so a resumed round moves its own workspace .hoh aside; the fully-complete resume calls start_round_game at :1071 and returns at :1076, launching and stopping a game session for no work; nothing restores or validates the interrupted iteration's partial edits; and the project is never checked against the run id. See AC-6/AC-7."
  },
  {
   "id": "I8-cfg-windows-test-defect",
   "pass": true,
   "evidence": "tests/brp_connection_pool.rs: a_client_rebuilt_for_the_new_process_succeeds_on_its_first_call now begins with `if !cfg!(windows) { println!(...); return; }`, the same guard its sibling a_pooled_connection_to_a_closed_peer_fails_the_next_call already had, with the reason (the abortive close SO_LINGER 0 is Windows-only)."
  },
  {
   "id": "I9a-tree-gate-green",
   "pass": true,
   "evidence": "cwd F:/moonbit-hof-rs, CARGO_TARGET_DIR=F:/hof-acc5-target (my own); cargo test --offline literal exit code 0; 754 passed / 0 failed / 6 ignored / 760 listed over 58 'test result:' lines; 0 occurrences of 'warning:' in stdout and stderr; cargo test --offline -- --list exit 0 with 760 names; --list --ignored exit 0 with exactly the 6 real-engine tests; cargo fmt --all --check exit 0 with 0 bytes of output; the whole sequence ran as one script in one build directory and tasklist showed no cargo/rustc/hoh/game process and no listener on 15702/15703 before or after."
  },
  {
   "id": "I9b-no-test-removed",
   "pass": true,
   "evidence": "Against the previous acceptance's independently recorded 740-name list (F:/hof-r4c-logs/gate-after-list.out), exactly two names disappear: godot_dev_skill_is_a_real_recipe_book and godot_testing_skill_explains_the_battery_and_relative_paths; both are replaced by the_bevy_dev_skill_is_a_real_recipe_book and the_bevy_testing_skill_explains_the_battery_and_relative_paths, present in the new list. 22 names added; 740 - 2 + 22 = 760. A literal name-set comparison therefore shows two removals, but the coverage of both tests is retained and extended in the renamed tests."
  },
  {
   "id": "I10a-adversarial-context-compaction",
   "pass": true,
   "evidence": "My own checks over all three recorded trajectories, every recorded call and tails 0/2/4/6/8/12/16/24/32: the fold never changes the message count, never grows any message, never touches messages[0]/[1] or the last `tail`, preserves every tool_calls id (call/result pairing), and the tail-bytes curve is monotone in the tail. No information-loss or ordering defect found in the fold itself. The separate claim that the fold lands on the agent's own history is false (AC-8)."
  },
  {
   "id": "I10b-adversarial-resume-wrong-state",
   "pass": false,
   "evidence": "Attempt to make --resume run into a wrong state succeeded at the code level in three ways: (1) the previous-evidence quarantine runs on resume, so the interrupted round's own .hoh (scratch, .hoh/deterministic/raw/**, injected skill copies) is moved to runs/<id>/quarantine/ before the incomplete iteration re-runs; the skipping path does not restore it. (2) Nothing rolls the workspace back or validates it, so the re-run starts on that iteration's own partial edits; a process killed inside std::fs::write can leave a truncated source that the iteration adopts. (3) Nothing compares --project with the run id (RunMeta has no project path), so a resume can continue run X against an unrelated workspace Y. See AC-6/AC-7."
  },
  {
   "id": "I11a-no-key-shaped-material",
   "pass": true,
   "evidence": "I re-implemented the repository's own shape rule (prefixes sk-/sk_/pk-/pk_/ghp_/gho_/xoxb-/xoxp-/AKIA/AIza with >=16 body chars, or an assignment name with a >=32-char value) in Python and scanned all 180 index-listed files and the 182-file browsable tree: the only hits are two declared fixtures inside tests/credential_scan.rs (the file is the repository's declared FIXTURE_SOURCES entry) and nothing else; values were fingerprinted, never printed. The two known gitignored historical files still exist and both carry the same token fingerprint 5cf81e8f (my own sha256), matching the previous acceptance. config/model.secret.env does not exist."
  },
  {
   "id": "I11b-secrets-load-only-from-outside",
   "pass": true,
   "evidence": "config/hoh.yaml carries no api_key value (only the comment that it must be empty); src/runtime/secrets.rs's ensure_secret_file_is_outside refuses a path inside the repository, and the round used --env-from-secret with a path outside the tree; the refusal and the load are pinned by tests/credential_scan.rs, green in my gate."
  },
  {
   "id": "I11c-frozen-documents-unmodified",
   "pass": false,
   "evidence": "All of REQUIREMENTS.md, PRD.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md, both spike reports, the B1/B2/B3 reports and acceptances, ROUND-1/2/3/4 reports, TRUST, STRIP, WRITE-PATH and ACCEPTANCE-ROUNDS are byte-identical to HEAD (git diff --stat empty). The one exception is .spec/bevy/ROUND-4-REPORT-COMPLETE.md, which is modified (one line: the RA-2 frame citation), and which the previous acceptance treated as a frozen report. The modification is disclosed in COST-REPORT.md; it is filed as AC-12 because the constraint as stated is not literally satisfied."
  },
  {
   "id": "I11d-tree-scope-and-nothing-pushed",
   "pass": true,
   "evidence": "The worktree is the harness plus the Bevy flow: src/adapter/ contains bevy/, engine.rs, mcp/, mod.rs, test_adapter.rs; src/prompts/skills/ contains only bevy-dev.md and bevy-testing.md; the Godot adapter module and the Godot-only tests remain removed (commit 14bd50f). 180 files are in the index at HEAD (the acceptance commit a1f51f1 added ACCEPTANCE-ROUNDS.md; the two skill deletions are unstaged and therefore still listed by git ls-files). No local ref has an upstream; refs/remotes/origin/master is still 6553afe (2026-10-04), older than master ba3d5c1 and bevy-core a1f51f1, so no Bevy work is pushed. I did not stage, commit or push anything."
  }
 ],
 "defects": [
  {
   "id": "AC-1",
   "severity": "medium",
   "what": "RA-1's false ordering claim survives in the frozen round reports while COST-REPORT says it was corrected there: .spec/bevy/ROUND-4-REPORT-COMPLETE.md:73 ('written by the harness before the spawn') and :131 ('which the harness wrote BEFORE the spawn'), and .spec/bevy/ROUND-3-REPORT.md:140. The code, the ledger note and all source docs are now correct; the record's reader is still told the wrong ordering, and the report's disposition is inaccurate.",
   "reproduction": "grep -n 'before the spawn' .spec/bevy/ROUND-4-REPORT-COMPLETE.md .spec/bevy/ROUND-3-REPORT.md; git diff .spec/bevy/ROUND-4-REPORT-COMPLETE.md shows a single hunk (the RA-2 frame line). README of the report: .spec/bevy/COST-REPORT.md:84 and :199."
  },
  {
   "id": "AC-2",
   "severity": "low",
   "what": "DECISIONS.md's appended entries cite an entry that does not exist: D298 references 'D301' twice and D299 once, but the batch's third entry is D300 and no D301 heading exists. A reader following the audit trail hits a dead reference.",
   "reproduction": "grep -n 'D301' DECISIONS.md -> lines 11286, 11293, 11329; grep -n '^## D3' DECISIONS.md -> D298, D299, D300."
  },
  {
   "id": "AC-3",
   "severity": "low",
   "what": "D298's measured cost formula and its system-prompt share do not match this batch's own measurement: it records 'prompt token ~= 4187 + 0.28 x cumulative wire bytes' and 'the system prompt is about 5% of the final prompt', while the round-5 fit is slope 0.255366 with intercept -38.28 and the system prompt is 14,814/161,566 = 9.2% of iter-2's final prompt (about a third after the fold).",
   "reproduction": "DECISIONS.md:11280-11284 (D298 (e)); F:/hof-acc5-logs/ctx.out (slope=0.255366 intercept=-38.28); COST-REPORT.md section 1.1 (14,814 wire bytes, 9%)."
  },
  {
   "id": "AC-4",
   "severity": "low",
   "what": "The RA-4 disposition overstates the new discrimination. For every launch that returns, readiness has already required answered_nonce == nonce and a non-empty nonce, so two of the three terms of identity.verified are invariants and the field's discriminating power is the OS TCP-table reading alone - the property D298 explicitly rejected. The report says 'Six cases pinned, each false for a launch that really occurs', but the mismatched/absent answered_nonce cases cannot occur on a returned launch; only the listening_pid cases can.",
   "reproduction": "src/adapter/bevy/launch.rs:502-529 (the only arm that sets answered_nonce is the equality arm; a mismatch returns LaunchError::IdentityMismatch and stops the child, so no LaunchFacts is produced); src/adapter/bevy/round.rs:820-835; the test the_identity_fields_are_computed_from_the_facts_not_asserted builds the impossible cases by hand."
  },
  {
   "id": "AC-5",
   "severity": "low",
   "what": "COST-REPORT's RA-7 disposition says the defect 'could not be located in this batch's copy of ACCEPTANCE-ROUNDS.md'; RA-7 is present at .spec/bevy/ACCEPTANCE-ROUNDS.md:137 and is, in substance, closed by D299. The disposition understates what the batch actually did.",
   "reproduction": "grep -n 'RA-7' .spec/bevy/ACCEPTANCE-ROUNDS.md -> line 137; .spec/bevy/COST-REPORT.md:90."
  },
  {
   "id": "AC-6",
   "severity": "medium",
   "what": "--resume runs the previous-evidence quarantine and starts the round's game session before doing any resume logic. quarantining moves the resumed round's own workspace .hoh (including .hoh/scratch/** and .hoh/deterministic/raw/**) to runs/<id>/quarantine/, and a fully-complete resume launches and then stops a game process although it executes no iteration. The batch's report and the CLI help do not mention either side effect.",
   "reproduction": "src/runtime/run_loop.rs:914 quarantine_previous_evidence (unconditional), :934 the resume branch that runs after it, :1071 start_round_game, :1076 the early return for a fully-complete resume; hygiene.rs:556 QUARANTINE_AREAS = [\".hoh\"] (ARTIFACT_DIR at hygiene.rs:509). Not executed (no round was run): established from the code path, which the new tests do not cover."
  },
  {
   "id": "AC-7",
   "severity": "medium",
   "what": "--resume can run into a wrong state in two further ways. (a) It never restores or validates the workspace, so the first incomplete iteration re-runs on top of its own partial edits - including a file truncated by a process death inside std::fs::write - while the code, the CLI help and the resume warning all say it 'runs from its start'; only the call grain is refused, not the dirty tree. (b) Nothing ties --project to --run-id: RunMeta has no project path, so 'hoh run --resume --run-id X --project Y' proceeds against Y while reading X's completed iterations.",
   "reproduction": "src/runtime/run_loop.rs:1019-1035 (A0 read from the index, no restore), :1087-1104 (skip path), and the absence of any workspace/project comparison in run_inner; src/runtime/record.rs:14-32 RunMeta has no project field; cli_impl.rs's --resume preconditions check only existence and mutual exclusion with --fresh-workspace/--reset-workspace. Not executed: established from the code path."
  },
  {
   "id": "AC-8",
   "severity": "medium",
   "what": "The fold is NOT applied to the agent's own history, so the trajectory does not record what was sent - the opposite of what three places claim. CompactedModel::query folds a local copy (messages.to_vec()) and passes that to the inner model; DefaultAgent::query stores the un-folded response in self.messages, which is what save() serialises. Effect: in a folded run the stored trajectory overstates the wire context and an auditor can no longer recompute what the provider was charged for from the record.",
   "reproduction": "src/harness/compact.rs:29-30 and :289-303 (the claim and the copy); /f/RustProjects/mini-swe-agent-rust-mini/rust/src/agent.rs:174-176 (InnerAgent::query pushes the model response into self.messages and never sees the folded copy) and :217-232 (serialize writes self.messages). The same claim appears at DECISIONS.md:11371-11372 and .spec/bevy/COST-REPORT.md:139-140. Note the tests/context_compaction.rs method depends on the trajectory being un-folded, so the code and the test are coherent and only the prose is wrong."
  },
  {
   "id": "AC-9",
   "severity": "low",
   "what": "src/config.rs quotes a projection the measurement contradicts: 'the projection over the three recorded round-4 Developer calls is 839K / 2.50M / 1.48M prompt tokens at a tail of 12'. The measured values are 875,647 / 2,681,282 / 1,663,325 (-4.2% / -6.8% / -11.0%).",
   "reproduction": "grep -n '839K' src/config.rs; F:/hof-acc5-logs/ctx.out and my independent F:/hof-acc5-work/measure.py both print the measured values."
  },
  {
   "id": "AC-10",
   "severity": "low",
   "what": "The headline reduction '20,940,837 -> 5,219,854 (25.5%)' is not like-for-like: the before figure is prompt+completion, the after figure is prompt-only. Prompt-only the reduction is 74.47%; adding the unchanged completion tokens back gives about 5.71M and about 72.7%. The three after-figures also sum to 5,220,254, not the quoted 5,219,854.",
   "reproduction": ".spec/bevy/COST-REPORT.md context_measurement.per_developer_call and projected_round; runs/round4/iter-*/result.json (completion tokens 81,632 / 325,953 / 86,121); F:/hof-acc5-work/claims.py."
  },
  {
   "id": "AC-11",
   "severity": "low",
   "what": "The report's 'declared, not fixed' list for previous-engine residue names only the engine-identity strings, but production code still carries the old engine's tool names in EXAMPLE_PREFERENCE (src/tools/index.rs:120-131), and old-engine names also appear in #[cfg(test)] code in src/runtime/policy.rs and src/tools/endpoint.rs. None of it is delivered to a role (a Bevy round's tools never match those names), but the binary contains them and the declaration is incomplete.",
   "reproduction": "python F:/hof-acc5-work/bincheck.py F:/hof-acc5-target/debug/hoh.exe -> editor_setup_collision_shape x2, project_create_script x2, running_game_get_node_property_samples x2, RectangleShape2D x1, godot-dev.md x0, godot-testing.md x0; src/tools/index.rs:120-131."
  },
  {
   "id": "AC-12",
   "severity": "low",
   "what": "A frozen document was modified: .spec/bevy/ROUND-4-REPORT-COMPLETE.md (one line, the RA-2 frame correction). It is the documented, disclosed correction of a factual error and it does not fabricate evidence, but the stated constraint 'the frozen documents unmodified' is not literally satisfied for that file.",
   "reproduction": "git diff -- .spec/bevy/ROUND-4-REPORT-COMPLETE.md -> one hunk at line 832-838 ('frame 477' -> 'frame 495 ... corrected by the round-5 cost batch'); git diff --stat HEAD over every other frozen document is empty."
  },
  {
   "id": "AC-13",
   "severity": "low",
   "what": "tests/repeated_action.rs's round-5 counter uses the observation's byte *length* as the proxy for the guard's sha256 digest. It is a conservative over-approximation (two different outputs of equal length count as identical there but not in the guard), so every 'the new rule would not fire' conclusion is safe, but the printed 'identical_max' is not the guard's own count and could overstate it.",
   "reproduction": "tests/repeated_action.rs RecordedCall.observation_len and identical_repeats_since_last_write (compares observation_len); src/harness/guard.rs output_digest uses sha256_hex."
  },
  {
   "id": "AC-14",
   "severity": "low",
   "what": "config/hoh.yaml does not document the new agent.compact_history / compact_history_tail knobs, so a reader of the configuration cannot see that the fold is on (the values come from Rust defaults true/12). Every other behaviour-changing limit in the same section is documented in the file.",
   "reproduction": "grep -n 'compact_history' config/hoh.yaml -> no line; src/config.rs:142-186 supplies the defaults; config/hoh.yaml's agent section documents step_limit, wrap_up_steps, max_repeated_actions, steps_per_artifact, etc."
  }
 ],
 "risks": [
  "The ~74.5% reduction is a projection over recorded trajectories; no live call has produced the projected prompt tokens, and the fitted tokens-per-wire-byte ratio was calibrated on un-folded source/code text, whereas the post-fold context is mostly short JSON whose token density may be higher. The direction and size of that error are unmeasured.",
  "The fold replaces consumed payloads with a digest and a first line; a role may re-derive or re-read what it can no longer see. This is the batch's own stated behavioural risk and it cannot be settled offline.",
  "identity.verified now goes false when the OS TCP table cannot be parsed (a localised Windows state word, a missing netstat, a permissions failure) even for a launch whose nonce was proved over the wire; the field no longer means only 'identity proved'.",
  "With the tripwire restricted to byte-identical results, a producing Developer call is no longer bounded by it at 15; the binding limits are now the 150-step ceiling and the 3600 s wall clock, both of which previously allowed multi-million-token calls.",
  "--resume has never continued a real round: the skip/re-run arithmetic is pinned, but the loop's continue path, the quarantine interaction and the dirty-workspace behaviour are untested end to end.",
  "Six tests are still ignored in the gate and they are exactly the real-engine ones (contract on a live Bevy game, the readiness handshake, the client rebind across two launches); the launcher's identity handshake remains unexercised by the gate.",
  "The localised-state trade-off in RA-9 means the ONE independent OS reading can now be absent where it previously returned a (possibly wrong) pid; on a non-English Windows the identity record loses its corroboration rather than gaining a false one."
 ],
 "unverified": [
  "That a live Developer call now produces the projected prompt tokens, and that the role still behaves coherently with 12 verbatim messages: no round was run and no model was called.",
  "That --resume continues a real interrupted round correctly: only plan_resume is exercised by tests; the loop path is established from source. In particular I could not observe the quarantine side effect or a dirty-workspace re-run.",
  "The implementer's four reported plants (P1-P4, F:/hof-cost-logs/plants.json): I read their logs but did not (and must not) reproduce them by modifying the repository. The behaviours they pin are independently green in my gate and present in the source.",
  "Whether anything was ever pushed to a remote: verified from local refs only, because the acceptance is offline (bevy-core has no upstream and origin/master is still 6553afe).",
  "Round-4 report prose beyond the one corrected frame line: not audited, as the batch itself declares.",
  "Byte-exactness of mini's real request serialisation against message_wire_bytes for a future folded history: on the recorded data the fit reproduces each trajectory's prompt-token total to <0.01%, which validates the proxy there, but the folded bytes themselves have never been sent."
 ]
}

---

# ACCEPTANCE — the bevy round-5 cost batch (context fold, tripwire semantics, RA-1..RA-9, `--resume`, the tree gate)

- Date: 2026-10-05
- Acceptance agent: an independent subagent; no prior context; no implementer or dispatcher conclusion inherited
- Revision measured: branch `bevy-core`, **HEAD `a1f51f1`**, plus the batch's uncommitted worktree — **36 modified tracked paths, 2 deletions and 4 untracked additions** (`COST-REPORT.md`, `src/harness/compact.rs`, `tests/context_compaction.rs`, `tests/resume_round.rs`); the briefing's "forty-one changed paths" predates the appearance of `COST-REPORT.md`. The worktree was byte-frozen by me before measuring and is byte-identical at the end (`F:/hof-acc5-logs/freeze1.txt` = `freeze2.txt`, sha256 `20a40be3…`, 1,076 lines)
- Environment: offline; **no engine, no game, no network, no model call and no round was run**; nothing written under `runs/**`; no tracked file modified by me; my scripts and logs live under `F:/hof-acc5-work` and `F:/hof-acc5-logs`, my build directory is `F:/hof-acc5-target`
- My only write inside the repository is this file. Nothing was staged, committed or pushed; `rm -rf` was never used; no process was killed.

## 0. A correction to the briefing, before anything else

The briefing says the implementer **never produced its report** and "wrote nothing". That is not what the tree shows:
`.spec/bevy/COST-REPORT.md` (28,571 bytes, untracked) was written at **2026-10-05 15:11:35**, i.e. in the same
minute my session opened — my first directory listing (before 15:11:35) did not show it. So the batch *did* write a
report, and the acceptance was dispatched while the writer was still finishing (the same ordering error DECISIONS.md
records for batch B1). I verified the report's claims against the tree and the raw evidence and treat it as an
untrusted claim source, never as authority. Nothing in the tree changed after 15:11:35 (manifest equality above),
so the measurements below are all against one stable revision.

## 1. Per-item table

| # | Job | Judgement | What I established myself |
|---|---|---|---|
| 1 | cut per-call context growth; measure before/after on recorded trajectories | **reduction real; method sound; target not met** | I re-implemented `compact_history` in Python and reproduced the report's numbers to the unit: projected prompt tokens `875,647 / 2,681,282 / 1,663,325` against recorded `2,544,563 / 12,765,478 / 5,137,090`, and the whole tail curve (0/2/4/6/8/12/16/24/32). The repository's own test prints the same. Reduction **74.5 %** of recorded *prompt* tokens. **But the 1.5M/call target is not met: iter-2 still projects to 2.68M.** |
| 2 | make the repeated-action tripwire mean what it says | **pass** | `record_repeat` now counts only consecutive successes with a **sha256-identical** result since the last counted write. My re-measurement from the recorded trajectories: window maxima 16 / 15 / 17 (the aborting counts of round 4) but identical-result maxima 1 / 1 / 2, so **none of the three calls would be ended by the new rule**; round 2's grind is also no longer caught (22 → 2 identical). Pinned by two new guard tests plus the integration test. |
| 3 | RA-1 (ledger ordering) | **code fixed, claim not fully corrected** | `launch.rs:443 spawn → :465 append_ledger`; the note, `append_ledger`/`ledger_entry`/`reap_ledger` docs and the call-site comment now say *after the spawn*, and a test spawns a real child and asserts the wording. **But `ROUND-4-REPORT-COMPLETE.md` still says "written by the harness before the spawn" (line 73) and "wrote BEFORE the spawn" (line 131)**, and COST-REPORT claims that file now says otherwise. `ROUND-3-REPORT.md:140` still has the same claim (untouched, frozen). Defect **AC-1**. |
| 4 | RA-6 (old engine's prompts) | **pass** | `godot-dev.md`/`godot-testing.md` deleted from the worktree; `prompts::skills()` returns the two Bevy books only; the compiled `hoh.exe` contains **0** occurrences of `godot-dev.md`/`godot-testing.md`. The prompt-discipline tests were re-pointed at the Bevy books with *more* assertions (≥7 recipes, old-engine absence needles, a real `WriteGuardEnvironment` scratch writer); one needle (`editor_play_scene` in the skill) was dropped with a stated reason. Two test *names* changed (`godot_*` → `the_bevy_*`). |
| 5 | DECISIONS.md entries | **append-only: pass; accuracy: fail** | md5 of the first 11,268 lines = `04b816fd088f808b1d70cd19cc7158be` = md5 of `HEAD:DECISIONS.md`; file grew 11,268 → 11,414 lines; three entries appended (D298, D299, D300), nothing reordered. But **D298 and D299 cite a "D301" that does not exist** (the batch's entry is D300), and D298's cost formula (`4187 + 0.28×bytes`) and "system prompt ≈5 %" do not match this batch's own measurement (`-38.28 + 0.2554×bytes`, ~9 %). Defects **AC-2**, **AC-3**. |
| 6 | RA-2 frame citation | **pass** | `runs/bevy-round4/calls/0008-bevy_grounded.json` has `result.frame = 495`, `grounded = true`; the string `477` occurs in none of the 57 call files. The corrected line names the file and the frame. |
| 6 | RA-3 per-pass snapshot semantics | **pass** | `RoundStopReport::ledger_lines_at_sweep` (serde field) + `sweep_covers_ledger_line(line)` (`line > 0 && line <= lines`), written by `reap_round_processes`, pinned by a test that appends a later ledger line and asserts it is not covered. |
| 6 | RA-4 `identity.verified` discriminates | **pass, with an overstated claim** | `identity_fields` is now a conjunction; because readiness only returns after the nonce matches, `answered_nonce == nonce` for **every** returned launch, so the operative term is `listening_pid == spawned_pid` — the OS reading. It *can* now be false for a real launch (different/absent listener), which is real discrimination. But the test/report claim that six cases are "launches that really occur" is false: a mismatched or missing `answered_nonce` cannot reach `launch.json`. Defect **AC-4**. |
| 6 | RA-7 (no round-3/4 DECISIONS entry) | **substantively closed; disposition inaccurate** | RA-7 is plainly present in `ACCEPTANCE-ROUNDS.md:137`, and D299 is exactly "rounds 3 and 4" — so the defect is closed. But COST-REPORT says RA-7 "could not be located in this batch's copy", which is false. Defect **AC-5**. |
| 6 | RA-8 definitional steps | **pass** | `Observation.definitional`/`definitional_note` (`#[serde(default)]`) set for `e3_grounded_payload` and `e3_win_position`; `battery_records` appends `[definitional: …]` to the round's own record; pinned by a test with a non-definitional control. |
| 6 | RA-9 `parse_listener_pid` fallback | **pass** | The `candidate.get_or_insert(pid)` fallback is gone; a non-`LISTEN` row returns `None` (ESTABLISHED, TIME_WAIT, `ABHOEREN` all covered). Trade-off recorded as a risk: on a localised Windows the OS reading disappears and `verified` becomes false for a launch that did prove its nonce. |
| 7 | `--resume` | **implemented, with defects** | `plan_resume` is pure arithmetic over `iter-<n>/result.json` and five tests plus the warning pin it; CLI refuses a missing run dir and the two workspace modes. **But the resume path runs `quarantine_previous_evidence` unconditionally (run_loop.rs:914), moves the interrupted round's own `.hoh` into `runs/<id>/quarantine/`, never restores/validates the partial iteration's edits, and does not check that `--project` belongs to the run id.** Defects **AC-6**, **AC-7**. A live resume was not and could not be run; the report admits this. |
| 8 | `cfg!(windows)` test defect | **pass** | `a_client_rebuilt_for_the_new_process_succeeds_on_its_first_call` now returns early with an explanatory `println!` on non-Windows, matching its sibling's guard. |
| 9 | reproduce the gate | **pass** | `cargo test --offline`, my own `CARGO_TARGET_DIR=F:/hof-acc5-target`, literal exit **0**; **754 passed / 0 failed / 6 ignored / 760 listed** over **58** `test result:` lines; **0** `warning:` in stdout and stderr; `--list` exit 0 with 760 names; `--list --ignored` = the 6 real-engine tests; `cargo fmt --all --check` exit 0 with **0 bytes** of output; no second test process (single script, `tasklist` clean before/after, no listener on 15702/15703). |
| 9 | no test removed | **pass by coverage; 2 names removed by rename** | Against the previous acceptance's independently recorded 740-name list: exactly two names disappear, `godot_dev_skill_is_a_real_recipe_book` and `godot_testing_skill_explains_the_battery_and_relative_paths`, both replaced by `the_bevy_*` equivalents present in the new 760; 22 names added; 740 − 2 + 22 = 760. A literal name-set test therefore fails; a coverage test passes. |
| 10 | adversarial: context compaction | **no information loss found; one false claim** | On all three recorded trajectories, over all calls and tails 0..32: the fold never changes the message count, never grows a message, never touches the system/task/last-`tail` messages, preserves every `tool_calls` id, and the tail curve is monotone. **However the fold is applied to a copy, so the trajectory does not record what was sent** — the opposite of what three files claim. Defect **AC-8**. |
| 10 | adversarial: `--resume` | **fail** | See AC-6/AC-7: the resume can run on a workspace that still holds the interrupted iteration's partial (possibly truncated) edits, after having moved that iteration's own `.hoh` evidence away; and it accepts any `--project`. |
| 11 | hard constraints | **keys pass; frozen docs fail on one file; scope pass with residue; nothing pushed** | 0 key-shaped findings outside the one declared fixture source `tests/credential_scan.rs` and the two known gitignored evidence files (fingerprint `5cf81e8f`, both re-derived by me); `config/model.secret.env` absent; secrets load only from outside. **`ROUND-4-REPORT-COMPLETE.md` was modified** (one line, RA-2) — a round report the previous acceptance treated as frozen. The two Godot skill files are deleted, but old-engine tool *names* survive in production `EXAMPLE_PREFERENCE` (`src/tools/index.rs`). No ref has an upstream and `origin/master` is still `6553afe`, older than both local branches. |

## 2. The cost question, stated exactly

**What was measured, and how.** For every one of the 296 recorded round-4 Developer model calls, the message
prefix the agent held before the call is reconstructed from `runs/round4/iter-*/traj/developer.attempt1.json`; its
"wire size" is the JSON subset mini actually sends (role, content, tool_calls, tool_call_id); the provider's own
recorded `usage.prompt_tokens` is fitted against that size; the repository's own `compact_history` folds the same
prefix; and the compacted bytes are converted with the fitted ratio. I re-implemented the fold independently in
Python (`F:/hof-acc5-work/measure.py`) and ran the repository's own test with `--nocapture`; **both give the same
integers**, and my numbers for the report's published tail curve (7,339,794 / 7,877,330 / … / 15,807,809) match it
exactly.

| recorded Developer call | calls | prompt tokens recorded | projected after (tail 12) | reduction | last prompt before → after |
|---|---|---|---|---|---|
| round-4 iter-1 | 69 | 2,544,563 | **875,647** | 65.6 % | 46,801 → 14,920 |
| round-4 iter-2 | 125 | 12,765,478 | **2,681,282** | 79.0 % | 161,566 → 25,152 |
| round-4 iter-3 | 102 | 5,137,090 | **1,663,325** | 67.6 % | 66,002 → 23,705 |
| total | 296 | 20,447,131 (prompt) / 20,940,837 (incl. completion) | 5,220,254 | **74.5 %** | |

**Is the claimed reduction real?** As an arithmetic projection over recorded trajectories, yes — it reproduces
exactly and the method is disclosed. **Is the target met? No.** The on-record target is *below 1,500,000 tokens per
Developer call*; the projection leaves iter-2 at **2.68M**, 1.79× the target, iter-3 at 1.66M, and only iter-1
below it. The report, D300 and the code all say this plainly — the batch does not claim the target.

Three accuracy caveats inside the cost claim:
1. **`src/config.rs`'s quoted projection is wrong.** Its comment says `839K / 2.50M / 1.48M`; the measurement is
   `875,647 / 2,681,282 / 1,663,325` (off by −4.2 %, −6.8 %, −11.0 %). Defect **AC-9**.
2. **The headline "20,940,837 → 5,219,854 (25.5 %)" is not like-for-like**: the "before" includes completion
   tokens, the "after" is prompt-only. Prompt-to-prompt the reduction is 74.47 %; adding the (unchanged) completion
   tokens back gives ≈5.71M and ≈72.7 %. Also the three quoted after-figures sum to 5,220,254, not 5,219,854.
   Defect **AC-10** (low).
3. The projection's ratio is a fit over *unfolded source/code text*; the folded text is mostly short JSON, whose
   tokens-per-byte density is plausibly higher. The direction of that error is not measured, and the report
   correctly labels the whole thing a projection that no live call has confirmed.

## 3. My own counterexamples and boundary probes

1. **Can the new tripwire still end a producing call?** I applied the new rule (sha256-identical results) to the
   recorded trajectories: identical maxima 1 / 1 / 2 against a cap of 15, no abort in any of the three round-4
   calls, and none in round 2's 22-repeat grind either. I also read the rule's escape hatches: a *directive* write
   (`HOH_WRITE_FILE`, …) never enters the counter at all, while a counted artifact write clears it. The residual
   false-positive shape is narrow but real: a call that edits the workspace through the **shell** (not the write
   directive) and gets the same stdout 15 times will still be aborted, because only directive writes count as
   progress. Recorded as a risk, not a defect.
2. **Can the fold lose or duplicate information?** Message count, per-message size, the system/task/tail boundary
   and every `tool_calls` id were checked for all three trajectories at nine tail lengths: no violation, and the
   size curve is monotone in the tail. The fold also keeps `<returncode>` and the command head, and never removes a
   message.
3. **Does the trajectory record what was sent?** No. `CompactedModel::query` folds `messages.to_vec()` and sends
   the *copy*; `mini_swe_agent::DefaultAgent::query` (vendored, `agent.rs:174-176`) then pushes the un-folded
   response into `self.messages`, which is what `save()` serialises. So the record is the un-folded history and the
   provider receives a different one. This is decisive from the source; it cannot be shown from a record, because
   no round has run with the fold on. Defect **AC-8** — and note the `context_compaction` test's *method* depends on
   this being true, so the code is coherent and only the three prose claims are wrong.
4. **Can `identity.verified` be false for a genuinely proved launch?** Yes, and by design: the conjunction's only
   non-invariant term is `listening_pid == spawned_pid`. A localised Windows state word now yields `None` →
   `verified = false`, although readiness proved the nonce. I re-derived the two invariant terms from
   `launch.rs:502-529` (the `Ok(answered) if Some(&answered) == Some(&process.nonce)` arm is the only path that
   sets `answered_nonce` and returns).
5. **Can `--resume` run into a wrong state?** `plan_resume` is exact (tests pass: missing, failed, hole,
   fully-complete, empty). The loop around it is not: (a) `quarantine_previous_evidence(&workspace, &run_dir)` is
   called unconditionally at `run_loop.rs:914`, before the resume branch at :934 and the skip at :1091, so a resume
   moves this round's own `.hoh` (scratch, `.hoh/deterministic/raw/**`) into `runs/<id>/quarantine/`; a
   *fully-complete* resume additionally calls `start_round_game` at :1071 before returning at :1076, launching and
   stopping a game session that does nothing. (b) Nothing restores the workspace, so "the first incomplete
   iteration runs from its start" is true of the iteration and false of its working tree: a process killed
   mid-`fs::write` can leave a truncated source that the re-run adopts as its starting point. (c) `RunMeta` has no
   project path and `run_inner` uses `cfg.runtime.workspace` as given, so `hoh run --resume --run-id X --project Y`
   is not refused.
6. **Is the previous engine really gone from what a role receives?** I scanned the built `hoh.exe`: 0 hits for
   `godot-dev.md`/`godot-testing.md`, but 2 hits each for `editor_setup_collision_shape`, `project_create_script`
   and `running_game_get_node_property_samples` — traced to the production constant `EXAMPLE_PREFERENCE`
   (`src/tools/index.rs:120-131`) and to `#[cfg(test)]` code in `src/runtime/policy.rs` and `src/tools/endpoint.rs`.
   None of it is delivered to a role (the Bevy tools never match those names), but the report's
   "declared, not fixed" list names only the engine-identity strings. Defect **AC-11** (low).
7. **Was any frozen document touched?** Only `.spec/bevy/ROUND-4-REPORT-COMPLETE.md` (one line). Every other
   document named in the constraint is byte-identical to HEAD.
8. **Two smaller accuracy probes.** The round-5 counter in `tests/repeated_action.rs` compares observations by
   **byte length**, not by the guard's sha256, so its printed "identical" maxima are an upper bound rather than the
   guard's own count — conservative, and it does not change any conclusion (AC-13). And `config/hoh.yaml` never
   documents the new `compact_history` knobs, so the fold's being on is visible only in `src/config.rs` (AC-14).

## 4. What I could not establish

* **A live call.** No round was run (and none could be, offline): the projected 18,300 tokens/call and the
  behaviour of a role that no longer sees folded-away payloads are unmeasured. This is the batch's own stated
  limitation and it is the right one; it is also the reason the cost criterion can only be *projected*, never
  *met*.
* **A live `--resume`.** The skip/re-run decision is pinned as pure arithmetic; the loop's `continue` path, the
  quarantine interaction and the dirty-workspace behaviour are established from source, not from a run.
* **The remote.** Whether anything was ever pushed is verified from local refs only (offline): `bevy-core` has no
  upstream, `origin/master` is still `6553afe`, older than both local branches.
* **The implementer's process.** Because there is no completion message, I cannot say whether the plants it reports
  (P1–P4, `F:/hof-cost-logs/plants.json`) were made on a frozen tree, nor whether the "green-before" runs preceded
  the edits. I read the logs it left; I did not reproduce a plant (that would have required modifying the
  repository, which is out of scope for acceptance). The batch's *tests* are independently green in my gate and the
  behaviour they pin is present in the source, so the plants are corroboration I did not need.
* **Round-4 report prose beyond the one corrected line** — not audited, as the report itself declares.

## 5. Independent judgement

The gate is green on a tree I built and tested myself: exit 0, 754/0/6/760 over 58 targets, zero warnings,
`fmt --check` clean, no second test process, and the test set grew while losing no coverage. The context fold is a
real, independently reproducible ~74.5 % reduction of the recorded Developer prompt tokens, its arithmetic is
honest and its scope is stated; the tripwire now means what its name says and the recorded round-4 calls would no
longer be cut by it; RA-2, RA-3, RA-6, RA-8, RA-9 and the `cfg!(windows)` defect are genuinely fixed; DECISIONS.md
is append-only. Those are the batch's real achievements.

Against that: **the criterion that failed last time still fails.** Even on the batch's own projection the
per-call target of 1.5M is missed by iter-2 (2.68M) and iter-3 (1.66M); the reduction is real but the target is
not met, and the batch says so itself. And four claims do not survive contact with the tree: the report says
`ROUND-4-REPORT-COMPLETE.md` was corrected for RA-1 when it still carries both false orderings; three files claim
the fold lands on the agent's own history when it lands on a copy (so the trajectory no longer records what was
sent); `src/config.rs` quotes a projection the measurement contradicts; and RA-7 is declared "not located" though
it is in the acceptance at line 137. `--resume` exists and its arithmetic is right, but its loop moves the
interrupted round's own evidence aside and can re-run an iteration on top of that iteration's partial edits,
without checking that the project it was pointed at is the one the run id belongs to.

I therefore return **fail** — not because the batch is empty (it is the largest and most competent of the cost
attempts, and its reduction is the first real move toward the target), but because the specific criterion that was
already failing is still not met, and because an acceptance that passed the batch would have to accept four
false statements and a resume whose side effects the batch's own report never mentions.

## 6. Reproduction

* Freeze/equality: `F:/hof-acc5-logs/freeze1.txt`, `freeze2.txt` (identical, sha256 `20a40be3…`).
* Gate: `F:/hof-acc5-logs/gate.{out,err,exit}`, `list.{out,exit}`, `list-ignored.{out,exit}`, `fmt.{out,err,exit}`; script `F:/hof-acc5-work/gate.sh`; parser `parse_gate.py`.
* Cost: my independent fold `F:/hof-acc5-work/measure.py`, adversarial checks `adv_fold.py`, claim comparison `claims.py`; repository output `F:/hof-acc5-logs/ctx.out` (`cargo test --test context_compaction -- --nocapture`).
* Tripwire: `F:/hof-acc5-logs/rep.out` (`cargo test --test repeated_action -- --nocapture`).
* Resume unit tests: `F:/hof-acc5-logs/resume.out`. Fold unit tests: `compactlib.out`.
* Keys: `keyscan.py` (0 findings outside the declared fixture source and the two gitignored files), `fp.py` (both historical files fingerprint `5cf81e8f`), `bincheck.py` (the built `hoh.exe`).
* Economics: `econ.py` (296 Developer calls, 20,940,837 tokens).
* Evidence read: `runs/round4/iter-*/{result.json,traj/developer.attempt1.json}`, `runs/bevy-round4/calls/0008-bevy_grounded.json`, `runs/bevy-round4/launch-ledger.jsonl`.
