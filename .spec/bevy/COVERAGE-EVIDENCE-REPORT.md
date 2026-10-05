```json
{
 "schema": "hof-rs / bevy round-1 PRD-coverage and evidence-reproducibility batch",
 "produced_at": "2026-10-05",
 "branch": "bevy-core",
 "head_at_start": "05604b9",
 "working_tree_at_end": "UNCOMMITTED: this batch was instructed not to commit; the delegating agent commits and pushes. `git status --porcelain` lists the changed files below plus `evidence/`.",
 "rounds_run": 0,
 "developer_calls_run": 0,
 "gate": {
  "command": "cargo test --offline",
  "literal_exit_code": 0,
  "exit_code_source": "the literal $? of that command, written to F:/hof-cov-work/gate.exit by the runner",
  "passed": 800,
  "failed": 0,
  "ignored": 6,
  "listed": 806,
  "test_result_lines": 60,
  "listed_equals_passed_plus_ignored": true,
  "start_tree_measured_at_HEAD": {
   "passed": 782,
   "failed": 0,
   "ignored": 6,
   "listed": 788
  },
  "delta_to_start_tree": {
   "passed": 18,
   "listed": 18,
   "added": 18,
   "removed": 0
  },
  "tests_removed": 0,
  "list_command": "cargo test --offline -- --list",
  "list_exit_code": 0,
  "list_count": 806,
  "list_ignored_exit_code": 0,
  "list_ignored_count": 6,
  "list_ignored_names": [
   "the_pinned_endpoint_answers_discover_with_the_23_methods_of_bevy_0191",
   "the_real_machine_smoke_proves_the_contract_on_a_live_bevy_game",
   "the_five_behaviours_are_observed_on_a_real_bevy_game_process",
   "a_client_rebuilt_for_the_new_process_answers_on_its_first_call",
   "the_adapter_rebinds_its_observing_client_at_every_launch",
   "the_round_three_transport_failure_reproduces_through_one_client"
  ],
  "fmt_command": "cargo fmt --all --check",
  "fmt_exit_code": 0,
  "fmt_stdout_bytes": 0,
  "fmt_stderr_bytes": 0,
  "warning_lines_stdout_and_stderr": 0,
  "build_dir": "F:/hof-cov-target (this batch's own; the repository's target/ was not used)",
  "no_second_test_process": "tasklist showed no cargo/rustc/hoh before or after the gate run",
  "free_space_checked_first": {
   "F:": "66 G free at the start, 57 G after",
   "D:": "252 G free"
  }
 },
 "coverage": {
  "denominator": "the frozen PRD's own surfaces, a compile-time constant",
  "denominator_source": "src/adapter/bevy/prd_surfaces.rs::PRD_SURFACES (19 items)",
  "not_the_denominator": "the Tester's claim count, which produced round 4's self-referential 6/8 (the acceptance's RA-5)",
  "registry": {
   "total": 19,
   "ids": [
    "P1",
    "P2",
    "P3",
    "P4",
    "P5",
    "C1",
    "C2",
    "C3",
    "C4",
    "C5",
    "C6",
    "Q-scale",
    "Q-startup",
    "Q-not-required",
    "Q-perf",
    "B2.1",
    "B2.2",
    "B2.3",
    "B2.4"
   ],
   "anchored_to_the_frozen_prd": "every id carries a literal anchor that must occur in .spec/bevy/PRD.md; tests/prd_coverage.rs::the_prd_surface_registry_is_anchored_to_the_frozen_prd recomputes all 19",
   "comparable_between_rounds": "the denominator is constant, so two rounds compare directly"
  },
  "items": [
   {
    "id": "P1",
    "status": "verified",
    "evidence": "battery steps: e3_movement, e3_movement_left, e3_movement_release",
    "reason": null
   },
   {
    "id": "P2",
    "status": "verified",
    "evidence": "battery steps: e3_coin_counter",
    "reason": null
   },
   {
    "id": "P3",
    "status": "verified",
    "evidence": "battery steps: e3_win_flag, e3_win_position",
    "reason": null
   },
   {
    "id": "P4",
    "status": "verified",
    "evidence": "battery steps: e3_jump_arc",
    "reason": null
   },
   {
    "id": "P5",
    "status": "verified",
    "evidence": "battery steps: e3_grounded, e3_grounded_payload",
    "reason": null
   },
   {
    "id": "C1",
    "status": "verified",
    "evidence": "battery steps: editor_errors_baseline, play_scene_ready",
    "reason": null
   },
   {
    "id": "C2",
    "status": "verified",
    "evidence": "battery step: editor_errors_baseline (its observation names the 8 declared contract type paths it compared against the frozen list)",
    "reason": null
   },
   {
    "id": "C3",
    "status": "verified",
    "evidence": "battery steps: e3_movement, e3_movement_release",
    "reason": null
   },
   {
    "id": "C4",
    "status": "verified",
    "evidence": "frozen invariant: the thin MCP layer sends one JSON-RPC request per call; every committed raw call file reuses its call's own sequence id across its BRP sub-requests, and a batch may not carry two requests with the same id (tests/evidence_reproduction.rs::the_committed_raw_calls_are_single_jsonrpc_requests)",
    "reason": null
   },
   {
    "id": "C5",
    "status": "unobservable",
    "evidence": "not decidable from the harness's own evidence",
    "reason": "the harness can prove that every criterion's evidence comes from a registered reflectable surface (that is C2), but it cannot enumerate a game's internal state to prove no key state lives outside one. Named here rather than omitted."
   },
   {
    "id": "C6",
    "status": "unobservable",
    "evidence": "not decidable from the harness's own evidence",
    "reason": "a NON-requirement: the PRD states that screenshots are not required, so no observation of a game can satisfy it and none should try. It is a scope statement about the frozen document."
   },
   {
    "id": "Q-scale",
    "status": "unobservable",
    "evidence": "not decidable from the harness's own evidence",
    "reason": "no frozen surface describes a scene's geometry, its level count or whether art assets were used, so 'the scale is small enough' is not decidable in-process."
   },
   {
    "id": "Q-startup",
    "status": "gap",
    "evidence": "battery steps: play_scene_ready, e3_process_liveness",
    "reason": "the recorded round-4 pass predates e3_process_liveness, so the harness recorded no step `e3_process_liveness` for it. CLOSED for any round that runs the ten-step battery."
   },
   {
    "id": "Q-not-required",
    "status": "unobservable",
    "evidence": "not decidable from the harness's own evidence",
    "reason": "a NON-requirement: the absence of a feature is not positively observable by a harness that can only read state the game declares."
   },
   {
    "id": "Q-perf",
    "status": "verified",
    "evidence": "battery step: e3_jump_arc",
    "reason": null
   },
   {
    "id": "B2.1",
    "status": "gap",
    "evidence": "battery steps: e3_process_liveness",
    "reason": "same as Q-startup: the recorded round predates the step that decides it. CLOSED for any round that runs the ten-step battery."
   },
   {
    "id": "B2.2",
    "status": "verified",
    "evidence": "battery step: editor_errors_baseline (BevyAdapter::prepare refuses a differently-named crate before any build step can run)",
    "reason": null
   },
   {
    "id": "B2.3",
    "status": "verified",
    "evidence": "frozen invariant: crate::adapter::mcp::TOOL_LIST_SHA256 pins the whole tool list including output schemas; tests/tool_discovery.rs recomputes it",
    "reason": null
   },
   {
    "id": "B2.4",
    "status": "verified",
    "evidence": "frozen invariant: src/adapter/bevy/prd.rs seals every byte above the PRD's seal marker; tests/bevy_adapter_b2.rs::the_prd_sealed_prefix_is_byte_identical recomputes it",
    "reason": null
   }
  ],
  "recorded_round_four_evidence": {
   "verified": 13,
   "total": 19,
   "gap": 2,
   "unobservable": 4,
   "decidable": 15,
   "gap_ids": [
    "Q-startup",
    "B2.1"
   ],
   "read_from": "evidence/observation/round4/deterministic/battery.json (11 records: the two gate steps plus the nine E3 steps the round ran)",
   "reproduced_by": "cargo test --offline --test evidence_reproduction the_recorded_round_four_evidence_scores_against_the_registry"
  },
  "a_round_that_runs_the_ten_step_battery": {
   "verified": 15,
   "total": 19,
   "gap": 0,
   "unobservable": 4,
   "decidable": 15,
   "verified_share_of_decidable": 100.0
  },
  "gaps": [
   {
    "id": "P3-goal-x",
    "disposition": "NAMED, NOT CLOSED — and it is not a PRD surface",
    "what_the_tester_asked_for": "the goal entity's own world position as reflectable state, so that 'the player reached the goal' is checkable beyond the win flag flipping",
    "status": "unobservable within the frozen contract",
    "why": "the frozen contract (§3-C2, and 附录 B2.1) declares EIGHT reflectable semantic surfaces and none of them is a goal. Adding a ninth is a contract change, which this batch has no authority to make; the PRD and the tool list are not edited here.",
    "what_the_harness_CAN_show": "the PRD's own P3 IS decided: `e3_win_flag` (won false -> true, one way) plus `e3_win_position` — a player transform sample at or after the win frame, so the win is located in the world. That is the surface P3 names; the residual is the goal's own entity.",
    "published_at": "src/adapter/bevy/prd_surfaces.rs::RESIDUALS, and here",
    "counted_in_the_denominator": false
   },
   {
    "id": "S1-deterministic-step",
    "disposition": "CLOSED — by a real observation, not by loosening the definition",
    "what_the_tester_asked_for": "a persisted late-round liveness step under .hoh/deterministic/raw/",
    "status": "closed for every round that runs the ten-step battery",
    "how": "the new tenth battery step `e3_process_liveness` (observation `liveness`) runs LAST: bevy_wait_frames(1) reads the game's own frame counter, bevy_wait_frames(8) asks for eight more, and the step requires the delta to be at least eight. It writes Observation::frames and persists `.hoh/deterministic/raw/e3_process_liveness.json` with the verbatim calls.",
    "why_it_is_a_real_observation": "it uses the frozen `hof_game::contract::FrameCounter` surface and the existing `bevy_wait_frames` tool: no new contract surface, no new tool, no new configuration. A game whose counter does not move makes the step `ok = false` with the reason.",
    "decides": [
     "Q-startup",
     "B2.1"
    ],
    "counted_in_the_denominator": true
   }
  ],
  "residual_outside_the_denominator": [
   {
    "id": "P3-goal-x",
    "status": "unobservable within the frozen contract",
    "reason": "the goal entity's own position is not one of the eight frozen contract surfaces; adding a ninth is a contract change. The harness observes the player's world position at the win frame instead, which is what decides P3."
   },
   {
    "id": "S1-deterministic-step",
    "status": "closed by e3_process_liveness",
    "reason": "closed by the e3_process_liveness battery step, which decides Q-startup and B2.1."
   }
  ]
 },
 "reproducibility": {
  "criterion": "make the cost and observation conclusions reproducible from the repository",
  "added_to_the_repository": {
   "root": "evidence/",
   "files": 118,
   "bytes": 4771139,
   "mib": 4.55,
   "groups": [
    {
     "path": "evidence/cost",
     "files": 4,
     "bytes": 4166273,
     "what": "the four recorded Developer trajectories the cost analysis reads, byte-identical to runs/<run>/iter-<n>/traj/developer.attempt1.json"
    },
    {
     "path": "evidence/observation/round4/deterministic",
     "files": 37,
     "bytes": 222299,
     "what": "the workspace-side battery evidence (.hoh/deterministic/**)"
    },
    {
     "path": "evidence/observation/round4/round",
     "files": 70,
     "bytes": 326506,
     "what": "the round's own evidence directory (runs/bevy-round4/**): 57 raw MCP->BRP call files, the readings, the gate, the launch facts, the launch ledger"
    },
    {
     "path": "evidence/observation/round4/iter-1",
     "files": 2,
     "bytes": 16161,
     "what": "iteration 1's result.json and the Tester's evidence.json"
    },
    {
     "path": "evidence/observation/round4/iter-2",
     "files": 2,
     "bytes": 19128,
     "what": "iteration 2's result.json and the Tester's evidence.json"
    },
    {
     "path": "evidence/observation/round4/iter-3",
     "files": 2,
     "bytes": 18487,
     "what": "iteration 3's result.json and the Tester's evidence.json"
    },
    {
     "path": "evidence/observation/round4/meta.json",
     "files": 1,
     "bytes": 2285,
     "what": "the round's own meta.json"
    }
   ],
   "index": "evidence/index.json",
   "readme": "evidence/README.md",
   "tools": [
    {
     "path": "evidence/tools/build_evidence.py",
     "what": "the copier that produced the corpus"
    },
    {
     "path": "evidence/tools/keyscan.py",
     "what": "a transcription of src/runtime/secrets.rs's key-shape rule; it refuses a key-shaped file and fingerprints findings instead of printing them"
    }
   ]
  },
  "key_scan": {
   "rule": "src/runtime/secrets.rs::{key_shaped_tokens, looks_key_shaped}",
   "result": "every one of the 118 committed files is CLEAN: no key-shaped token (prefix + >= 16 token chars) and no key-shaped assignment (>= 32 chars)",
   "recomputed_by": "cargo test --offline --test credential_scan no_key_shaped_material_is_browsable_in_the_repository_tree",
   "redaction_finding": "the round-4 trajectories' `.redacted.json` sidecars differ from the raw ones by 187/180/180/977 bytes and the differences are <redacted> replacements of HOH_ARTIFACT_DIR / HOH_GAME_ROUTE / HOH_HOH_BIN env values (12 occurrences), NOT credentials. The raw files are key-scan clean and were committed as-is."
  },
  "index_of_headline_numbers": [
   {
    "headline": "cost.trajectories_total_bytes = 4,166,273",
    "files": [
     "evidence/cost/*.developer.attempt1.json"
    ],
    "command": "cargo test --offline --test evidence_reproduction the_committed_cost_corpus_is_the_recorded_one"
   },
   {
    "headline": "cost.live.total_tokens = 3,651,120 (150 calls) and 2.434x the target",
    "files": [
     "evidence/cost/livecost1-iter-1.developer.attempt1.json"
    ],
    "command": "cargo test --offline --test write_accounting the_live_calls_write_profile_is_the_corrected_one"
   },
   {
    "headline": "cost.round4.iter{1,2,3} tokens = 2,626,195 / 13,091,431 / 5,223,211",
    "files": [
     "evidence/cost/round4-iter-1.developer.attempt1.json",
     "evidence/cost/round4-iter-2.developer.attempt1.json",
     "evidence/cost/round4-iter-3.developer.attempt1.json"
    ],
    "command": "cargo test --offline --test write_accounting"
   },
   {
    "headline": "accounting.live.write_profile (directive [6,14,17,19,43]; project [6,14,17,19,43,44,95]; failed [[139, src\\game.rs, 1]])",
    "files": [
     "evidence/cost/livecost1-iter-1.developer.attempt1.json"
    ],
    "command": "cargo test --offline --test write_accounting the_live_calls_write_profile_is_the_corrected_one"
   },
   {
    "headline": "accounting.iter3.write_profile (directive [6,50,70,73,74,80,84,86,90,93,97]; project [6,8,75,81,85,87,91,94,98]; undecided [72])",
    "files": [
     "evidence/cost/round4-iter-3.developer.attempt1.json"
    ],
    "command": "cargo test --offline --test write_accounting the_recorded_iteration_three_write_timeline_is_the_corrected_one"
   },
   {
    "headline": "accounting.withdrawn_k32 (live 76 / 1,357,530 cutting project write 95; iter-3 39 / 1,604,038 cutting ten directives and seven project edits)",
    "files": [
     "evidence/cost/livecost1-iter-1.developer.attempt1.json",
     "evidence/cost/round4-iter-3.developer.attempt1.json"
    ],
    "command": "cargo test --offline --test write_accounting the_withdrawn_budget_at_k_32_cuts_ten_directives_and_seven_project_edits"
   },
   {
    "headline": "accounting.bands = 37 / 43 / 52 (D-1 restated)",
    "files": [
     "evidence/cost/livecost1-iter-1.developer.attempt1.json",
     "evidence/cost/round4-iter-3.developer.attempt1.json"
    ],
    "command": "cargo test --offline --test write_accounting the_global_safe_floor_is_fifty_two_and_not_forty_three"
   },
   {
    "headline": "coverage.registry = 19 stable ids anchored to the frozen PRD",
    "files": [
     "src/adapter/bevy/prd_surfaces.rs",
     ".spec/bevy/PRD.md"
    ],
    "command": "cargo test --offline --test prd_coverage the_prd_surface_registry_is_anchored_to_the_frozen_prd"
   },
   {
    "headline": "coverage.recorded_round4 = 13 / 19 (2 gaps, 4 unobservable)",
    "files": [
     "evidence/observation/round4/deterministic/battery.json"
    ],
    "command": "cargo test --offline --test evidence_reproduction the_recorded_round_four_evidence_scores_against_the_registry"
   },
   {
    "headline": "coverage.full_battery = 15 / 19 (0 gaps, 4 unobservable)",
    "files": [
     "src/adapter/bevy/prd_surfaces.rs",
     "src/adapter/bevy/round.rs"
    ],
    "command": "cargo test --offline --test evidence_reproduction the_full_battery_scores_the_registry"
   },
   {
    "headline": "observation.round4.raw_calls = 57 files, one semantic call each, no batch",
    "files": [
     "evidence/observation/round4/round/calls"
    ],
    "command": "cargo test --offline --test evidence_reproduction the_committed_raw_calls_are_single_jsonrpc_requests"
   },
   {
    "headline": "observation.round4.tester_claims = 6/8 each iteration, differently shaped",
    "files": [
     "evidence/observation/round4/iter-1/result.json",
     "evidence/observation/round4/iter-2/result.json",
     "evidence/observation/round4/iter-3/result.json"
    ],
    "command": "cargo test --offline --test evidence_reproduction the_recorded_tester_figures_are_the_self_referential_ones"
   },
   {
    "headline": "the index itself names only committed files",
    "files": [
     "evidence/index.json"
    ],
    "command": "cargo test --offline --test evidence_reproduction the_evidence_index_names_committed_files_and_commands"
   }
  ],
  "cannot_be_reproduced_from_the_repository": [
   {
    "conclusion": "the provider's own per-call usage for any call outside the four committed trajectories, and every figure in LIVE-COST-REPORT.md, COST-REPORT.md, FIX-REPORT.md and ROUND-4-REPORT-COMPLETE.md that rests on them",
    "why": "the committed 4,166,273 bytes are the four Developer trajectories; every other trajectory (the other roles, rounds 1-3, the five round-4 attempts) stays under the gitignored runs/** (11,229 files / 12,775,066,006 bytes / 11.898 GiB)"
   },
   {
    "conclusion": "byte-level identity of what a successful shell write put on disk",
    "why": "the recording proves a write ran and reported success; no committed file holds the file's bytes before and after"
   },
   {
    "conclusion": "the withdrawn step budget's behaviour on a live game, and whether a tree-fingerprint signal reaches the cost target",
    "why": "both need a live round; no offline replay may execute the recorded shell commands, and this batch ran none"
   },
   {
    "conclusion": "the .hoh/deterministic evidence of the five round-4 attempts other than the final one",
    "why": "the workspace at F:/hof-bevy-r4-run/workspace was overwritten by each pass; only the last pass's tree survives, and only it is committed"
   },
   {
    "conclusion": "the derivation that this corpus is a faithful subset of runs/**",
    "why": "the corpus is a copy; the copy is verified byte-for-byte against its source by evidence/tools/build_evidence.py's sha256 manifest, but the source is not in the repository, so a reader can only re-run the copier where the source exists"
   }
  ]
 },
 "defect_d_1_restatement": {
  "defect": "D-1 of .spec/bevy/ACCEPTANCE-ACCOUNTING.md — the safe-band floor is understated",
  "what_the_reports_said": "\"to cut no recorded work: K >= 43\" (LIVE-COST-REPORT.md section 4 and its machine block; WRITE-ACCOUNTING-REPORT.md the_two_bands.to_cut_no_recorded_work)",
  "why_it_is_wrong": "K >= 43 is round-4 iteration 3's DIRECTIVE window only. Under the corrected project-write accounting the live call's last directive write is call 43 and its last PROJECT write is call 95, so the rule fires at call 44 + K: every K <= 51 refuses a recorded project write. K = 50 fires at call 94 and cuts the call-95 write; K = 51 fires at call 95 itself and refuses that write (the after-list is empty because the write never happens, which is why the strict convention nearly hides it). K = 52 fires at call 96 and cuts nothing.",
  "corrected_threshold": {
   "cut_no_recorded_project_write_min_k": 52,
   "cut_no_recorded_project_write_min_k_strict_convention": 51,
   "iter3_directive_window_min_k": 43,
   "meet_the_criterion_max_k": 37
  },
  "conclusion_still_holds_and_is_stronger": "37 < 43 < 52: the bands still do not overlap, and the losing side is worse than the report said",
  "where_restated": [
   ".spec/bevy/LIVE-COST-REPORT.md (the machine block's to_cut_no_recorded_work, recomputed_with_the_corrected_accounting, gap and single_most_important_thing fields, plus sections 4 and 8)",
   ".spec/bevy/WRITE-ACCOUNTING-REPORT.md (the_two_bands, the_evaluation_still_in_force, what_the_recomputation_did_not_change, the decision statement and section 4)",
   "DECISIONS.md D305 (appended; DECISIONS.md is append-only and D303's text is intact)"
  ],
  "pinned_by": "tests/write_accounting.rs::the_global_safe_floor_is_fifty_two_and_not_forty_three (K = 50 -> call 94 with project write 95 after it; K = 51 -> call 95; K = 52 -> call 96 and nothing cut; every K in 1..=51 fires at or before call 95), and plant P4"
 },
 "plants": [
  {
   "id": "P1-a-missing-step-counts-as-verified",
   "file": "src/adapter/bevy/prd_surfaces.rs",
   "defect": "a surface whose battery step never ran is reported as verified — the exact false-green shape RA-5 was about",
   "test": "adapter::bevy::prd_surfaces::tests::a_step_the_pass_never_recorded_is_a_gap_that_names_it",
   "green_before_exit": 0,
   "red_exit": 101,
   "green_after_exit": 0,
   "red_ran": true,
   "red_named_test": true,
   "restore_byte_exact": true,
   "sha256_before": "659b8f997e6c1c64121e4998d0036c3ddcae569cf70cadf2a70539cd15f00412",
   "mtime_plant": 1791200000.0,
   "mtime_restore": 1791400000.0
  },
  {
   "id": "P2-the-liveness-verdict-ignores-the-advance",
   "file": "src/adapter/bevy/battery.rs",
   "defect": "a game whose frame counter never moved is reported as alive, silently re-opening the S1-deterministic-step gap this batch closes",
   "test": "adapter::bevy::battery::tests::the_liveness_verdict_reads_the_games_own_frame_advance",
   "green_before_exit": 0,
   "red_exit": 101,
   "green_after_exit": 0,
   "red_ran": true,
   "red_named_test": true,
   "restore_byte_exact": true,
   "sha256_before": "5e9b7a4b117044122805947be189ae8bbd621c29086dbdd280783820882c5ee3",
   "mtime_plant": 1791200000.0,
   "mtime_restore": 1791400000.0
  },
  {
   "id": "P3-the-liveness-step-is-dropped-from-the-battery",
   "file": "src/adapter/bevy/round.rs",
   "defect": "the observation the batch adds is dropped, so Q-startup and B2.1 name a step the battery does not run",
   "test": "adapter::bevy::round::tests::the_ten_e3_steps_name_the_prds_behaviours_and_keep_the_original_five",
   "green_before_exit": 0,
   "red_exit": 101,
   "green_after_exit": 0,
   "red_ran": true,
   "red_named_test": true,
   "restore_byte_exact": true,
   "sha256_before": "fee721181ae48f85ff1b50633ed0c69eee0082dd7b8cb6549860e9c9a7b8a246",
   "mtime_plant": 1791200000.0,
   "mtime_restore": 1791400000.0
  },
  {
   "id": "P4-the-replay-fires-one-call-early",
   "file": "src/harness/write_audit.rs",
   "defect": "the withdrawn budget's abort predicate is off by one call, which moves the global safe floor D-1 restates",
   "test": "the_global_safe_floor_is_fifty_two_and_not_forty_three",
   "green_before_exit": 0,
   "red_exit": 101,
   "green_after_exit": 0,
   "red_ran": true,
   "red_named_test": true,
   "restore_byte_exact": true,
   "sha256_before": "17d1dc4abe5f63ba9da679954bcc7a35bb216dcff195da52256d44e10afe8179",
   "mtime_plant": 1791200000.0,
   "mtime_restore": 1791400000.0
  }
 ],
 "changed_files": {
  "added": [
   "src/adapter/bevy/prd_surfaces.rs (the frozen PRD surface registry, the three deciders and the item-by-item verdict)",
   "tests/evidence_reproduction.rs (every headline number re-derived from evidence/ only)",
   "evidence/ (118 files / 4,771,139 bytes: the cost corpus, the round-4 observation corpus, the index, the README and the two tools)",
   ".spec/bevy/COVERAGE-EVIDENCE-REPORT.md (this file)"
  ],
  "modified": [
   "src/adapter/bevy/battery.rs (the liveness observation, FrameAdvance, LIVENESS_FRAMES, and the tenth named observation)",
   "src/adapter/bevy/round.rs (E3_STEPS gains e3_process_liveness with the stable PRD id Q-startup; the raw payload now carries `frames`)",
   "src/adapter/bevy/project.rs (the Bevy adapter decides the frozen surfaces)",
   "src/adapter/bevy/mod.rs (module declaration)",
   "src/adapter/mod.rs (ProjectAdapter::prd_surfaces, defaulting to the empty registry)",
   "src/model.rs (PrdSurfaceCoverage, PrdSurfaceVerdict, SurfaceStatus, PrdCoverage::surfaces, BatteryPassSummary::surfaces — all serde(default))",
   "src/runtime/run_loop.rs (the pass's own surface coverage travels with the pass)",
   "src/cli_impl.rs (the run summary line and the hoh status surfaces= column)",
   "src/prompts/skills/bevy-testing.md and the Bevy tester playbook (the new raw path)",
   "tests/prd_coverage.rs (the anchor test, the denominator test, the line test)",
   "tests/write_accounting.rs (reads evidence/cost/ first; the D-1 floor test)",
   ".spec/bevy/LIVE-COST-REPORT.md and .spec/bevy/WRITE-ACCOUNTING-REPORT.md (only where factually wrong: the D-1 bound)",
   "DECISIONS.md (D305 appended only: 1295073 -> 1306821 bytes, the old bytes are a byte prefix of the new file)"
  ],
  "not_modified": "REQUIREMENTS.md, PRD.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md, the spike reports, the batch reports, ACCEPTANCE-*.md, ROUND-*.md, COST-REPORT.md, config/hoh.yaml",
  "new_dependencies": "none",
  "source_code_behaviour_change": "none that changes a verdict: the surface coverage is published, not enforced; the only new battery work is one eight-frame wait at the end of a pass"
 },
 "provenance_note_on_a_quoted_byte_count": "The task that commissioned this batch quoted the four trajectories at 4,166,773 bytes; the files measure 4,166,273, which is what .spec/bevy/WRITE-ACCOUNTING-REPORT.md already records. The files are the authority and D305 corrects the other figure.",
 "unverified": [
  "That a clone actually rebuilds and runs the ten-step battery: no engine is reachable offline and this batch ran no round, so `e3_process_liveness` has never executed against a real game. Its unit surface, its fake-driver phase and its persistence path are tested; the live path is not.",
  "Whether the two record-4 gaps close on a real run: the recorded evidence cannot show it, because the recorded round predates the step.",
  "Whether an iteration-2-shaped Developer call is under the cost target — unchanged from the previous batch, and this batch ran no call.",
  "The lever pairs and the compact_history projections: not re-derived here.",
  "That the committed corpus is complete for every headline: index.json names a committed file for each of the 14 headlines it lists, and the test proves those files exist, but a headline nobody indexed would not be caught."
 ],
 "single_most_important_thing_next_batch": "Run ONE live round on this tree and read `result.json.prd_coverage.surfaces`. The figure is now a function of the frozen PRD's own 19 surfaces, the denominator cannot move between rounds, and the only expected gap is the four named unobservable items (C5, C6, Q-scale, Q-not-required). If a live round shows Q-startup or B2.1 red, the liveness step is measuring something real and failing honestly — which is the first time this project would have a PRD coverage figure that can be compared with the next round's. Do NOT treat 15/19 as 'five items short': four of the five are non-requirements or out of the harness's reach BY DESIGN, and they are named so that nobody can mistake them for missing claims."
}
```

# COVERAGE-EVIDENCE-REPORT — the PRD's own surfaces as the coverage denominator, the two round-4 gaps, and the part of the evidence that is now reproducible from the repository

Independent, **offline** work on `bevy-core` at `05604b9` (clean tree at the start). **No engine, no
game, no network, no model call, no round and no Developer call was run.** I did not write under
`runs/**`, did not construct a path from an unexpanded variable, did not use `git checkout --`, did not
use `rm -rf`, did not commit, stage or push, and did not request any approval. Every auxiliary script
lived outside the repository, under `F:\hof-cov-work\`.

The machine-readable block above is the first thing in this file. It is serialiser output
(`json.dumps` over a dict, `indent=1`), written by `F:/hof-cov-work/write_report.py` and then **parsed
back out of this written file**; the parse is the last thing the generator does and it fails the run if
the block does not round-trip.

## 0. The two criteria this batch is about, in one paragraph each

**Criterion (2), "decidable".** Round 4's `prd coverage: 6/8 verified` had a self-referential
denominator: no claim id was an `F<n>` id, so `PrdCoverage::total()` fell back to `verified + gap`,
i.e. **however many claims the Tester happened to write** (`.spec/bevy/ACCEPTANCE-ROUNDS.md` RA-5).
Round 4's `6/8` and round 3's `7/8` were therefore not comparable, and the figure said nothing about the
PRD. It is now a function of **19 stable ids anchored to the frozen `PRD.md`** — the document's own
`P1..P5` and `C1..C6`, the four §4 clauses it bolds, and 附录 B2's four subsections — each decided by the
harness's own battery evidence, by a frozen invariant recomputed by a named test, or by an explicitly
named reason why it cannot be decided. Testers can write two claims or twenty and the denominator does
not move. The two gaps the acceptance left open are now **decided**: `S1-deterministic-step` is
**closed by a new, real, persisted observation** (`e3_process_liveness`, the tenth battery step), and
`P3-goal-x` is **named as unobservable within the frozen contract** rather than silently dropped —
because the thing it asks for would be a ninth reflectable surface, and that is a contract change this
batch has no authority to make.

**Criterion (4), reproducibility.** The acceptance measured the recorded evidence at **11,229 files /
12,775,066,006 bytes / 11.898 GiB, entirely under a gitignored path** (R-2), and the project's own
criteria include keeping evidence and being reproducible. The whole tree is far too large to commit;
the parts the conclusions rest on are not. **`evidence/` is 118 files / 4,771,139 bytes (4.55 MiB)**:
the four Developer trajectories the cost analysis reads (4,166,273 bytes, byte-identical to their
`runs/**` originals), the round-4 workspace-side battery evidence (222,299 bytes), the round's own
evidence directory including its 57 raw MCP→BRP call files (326,506 bytes), the three iterations'
`result.json` + `evidence.json` (53,776 bytes) and the round's `meta.json` (2,285 bytes).
`evidence/index.json` states, for each of 14 headline numbers, **which committed files reproduce it and
by what command**, and which conclusions **cannot** be reproduced from the repository. A new test,
`tests/evidence_reproduction.rs`, re-derives the headlines from the committed files alone;
`tests/write_accounting.rs` now reads `evidence/cost/` first and only falls back to `runs/**`.
Nothing key-shaped is committed: every one of the 118 files was scanned with the repository's own
shape rule and is clean.

## 1. What I did, and with what

* I read the whole relevant record before writing anything: the acceptance that passed and its D-1,
  the write-accounting report, `ROUND-4-REPORT-COMPLETE.md`, `ACCEPTANCE-ROUNDS.md` (RA-5), the
  frozen `PRD.md` and `REQUIREMENTS.md`, `ACCEPTANCE-LIVE-COST.md`, `DECISIONS.md`, and the code under
  `src/`.
* I wrote the registry, the deciders and the tenth battery step test-first: the new tests were added
  and run red (the module did not exist), then the module was written, then the suite went green, then
  it was refactored under a green suite.
* I built the evidence corpus with a committed copier (`evidence/tools/build_evidence.py`) that
  key-scans every destination before writing it, using a transcription of
  `src/runtime/secrets.rs`'s own shape rule (`evidence/tools/keyscan.py`).
* I re-derived the cost headlines from the committed corpus in Python *before* pinning them in Rust,
  so the Rust test is a check on a number I had already measured, not the number itself.
* I ran the gate, `--list`, `--list --ignored` and `fmt --check` in this batch's own build directory
  (`F:/hof-cov-target`), and I ran four controlled plants.

## 2. The coverage figure, item by item

The denominator is `PRD_SURFACES` in `src/adapter/bevy/prd_surfaces.rs`: **19 items**, each carrying an
**anchor** — a literal that must occur in the frozen `.spec/bevy/PRD.md` — and a decider. The
`anchored_to_the_frozen_prd` test recomputes all 19 against the file, and `EXPECTED_IDS` spells the
denominator out, so a renamed or dropped surface is a red test rather than a quietly smaller
percentage.

| id | status on the recorded round-4 evidence | what decides it |
|---|---|---|
| `P1` | verified | `e3_movement`, `e3_movement_left`, `e3_movement_release` |
| `P2` | verified | `e3_coin_counter` |
| `P3` | verified | `e3_win_flag`, `e3_win_position` |
| `P4` | verified | `e3_jump_arc` |
| `P5` | verified | `e3_grounded`, `e3_grounded_payload` |
| `C1` | verified | `editor_errors_baseline`, `play_scene_ready` |
| `C2` | verified | `editor_errors_baseline` — its own observation names the **8 contract type paths** it compared against the frozen list |
| `C3` | verified | `e3_movement`, `e3_movement_release` |
| `C4` | verified | frozen invariant: one JSON-RPC request per call; each committed raw call file reuses its call's own sequence id across its sub-requests, and a batch may not carry two requests with the same id |
| `C5` | **unobservable** | named reason: the harness can prove every criterion's evidence comes from a registered surface, but it cannot enumerate a game's internals to prove no key state lives elsewhere |
| `C6` | **unobservable** | named reason: a **non-requirement** — the PRD says screenshots are not required, so no observation can satisfy it |
| `Q-scale` | **unobservable** | named reason: no frozen surface describes geometry, level count or art assets |
| `Q-startup` | **gap** (on the recorded round) | `play_scene_ready`, `e3_process_liveness` — the recorded round predates the second |
| `Q-not-required` | **unobservable** | named reason: a non-requirement; absence of a feature is not positively observable |
| `Q-perf` | verified | `e3_jump_arc` (an arc with rise **and** fall inside the poll budget is exactly the frame-rate claim) |
| `B2.1` | **gap** (on the recorded round) | `e3_process_liveness` |
| `B2.2` | verified | `editor_errors_baseline` — `prepare` refuses a differently-named crate before any build step can run |
| `B2.3` | verified | frozen invariant: `TOOL_LIST_SHA256` pins the whole list including `outputSchema` |
| `B2.4` | verified | frozen invariant: the PRD's append-only seal |

* **Recorded round-4 evidence: 13 verified / 2 gap / 4 unobservable of 19** (15 decidable). Both gaps
  are the surfaces the round predates the new step by. `cargo test --offline --test evidence_reproduction
  the_recorded_round_four_evidence_scores_against_the_registry` reads only
  `evidence/observation/round4/deterministic/battery.json`.
* **A round that runs the ten-step battery: 15 verified / 0 gap / 4 unobservable of 19** — 100 % of
  what is decidable. The four `unobservable` items are named gaps, not missing claims: `C5`, `C6`,
  `Q-scale`, `Q-not-required`.
* The Tester-derived figure still travels on the same line and in the same JSON, labelled for what it
  is (`OWN claim count`, `NOT the PRD surface count`, `not comparable`). Nothing was removed to make
  room; the two answer different questions and a reader can see both.

**The defect this closes is pinned by a test that cannot be satisfied by changing the Tester.**
`tests/prd_coverage.rs::the_surface_denominator_does_not_move_with_the_testers_claims` builds two
schema-valid evidence bundles — round 3's shape (3 verified / 2 gap, ids like `C1-launch`) and round
4's (6 verified / 2 gap, ids like `S1-deterministic-step`) — asserts that their Tester-derived figures
really differ (`5` vs `8`), and then asserts that both carry the same surface denominator, 19.

## 3. `P3-goal-x`: named as unobservable, not closed, and not in the denominator

The Tester asked for the **goal entity's own world position as reflectable state**, so that "the player
reached the goal" is checkable beyond the win flag flipping. The frozen contract
(`PRD.md` §3-C2, and 附录 B2.1 which took it from six surfaces to seven) declares **eight** reflectable
semantic surfaces, and **none of them is a goal**. Adding a ninth is a contract change — a re-frozen
contract hash, a re-frozen tool list, and the decision process the PRD's freeze rule names. This batch
has no authority to make that change, so it does not.

What the harness **can** show, and does, is the PRD's own `P3`: `e3_win_flag` proves `won` goes
false → true and never back, and `e3_win_position` takes a `PlayerTransform` sample at or after that
frame, so the win is **located in the world**. That is the surface `P3` names. The residual — the goal
entity's own coordinates, independent of where the player was — is recorded by name in
`prd_surfaces::RESIDUALS` and in the block above, with the reason, and it is deliberately **outside**
the 19-item denominator, because it is not a PRD surface.

**Is this "loosening the definition of the gap"?** No, and it is worth being explicit about why:
the gap as the Tester phrased it was **stricter than the frozen PRD**. Criterion (2) asks for the
coverage figure to be a function of the PRD's surfaces; re-anchoring `P3` to the surface the PRD
actually states is that change, not a relaxation of it. Nothing in the frozen documents was edited, no
tool was removed, and the residual is published so a reader can disagree with the disposition by
reading the reason rather than by guessing.

## 4. `S1-deterministic-step`: closed by a real observation

The Tester asked for **a persisted late-round liveness step under `.hoh/deterministic/raw/`**, and the
recorded round had none: the process being alive at the end of the pass was an assumption.

It is now a measurement. The tenth battery step, `e3_process_liveness` (observation name `liveness`,
supporting the stable id `Q-startup`), runs **last**:

1. `bevy_wait_frames(1)` — reads the game's own `hof_game::contract::FrameCounter`;
2. `bevy_wait_frames(8)` — asks the game for eight more frames;
3. the step requires the counter to have advanced by **at least** the eight that were asked for
   (`FrameAdvance::verdict`, unit-tested for all four shapes: exactly eight, more than eight, not at
   all, and a counter that moves less than requested — the last is the `B2.1` failure, where the number
   reported is not the game's own progress).

The result lands in `Observation::frames` and is persisted as
`.hoh/deterministic/raw/e3_process_liveness.json` with the verbatim requests and replies, exactly like
the other nine steps. **No new contract surface, no new tool and no new configuration are involved**:
the step uses the frozen `FrameCounter` surface and the existing `bevy_wait_frames`, which already
refuses to answer without advancing the counter. A game that has stopped stepping makes the step
`ok = false` with its reason, which turns `Q-startup` and `B2.1` into **gaps** rather than passes — and
plant P2 shows exactly that shape going red.

## 5. What was added for reproducibility, and what it buys

`evidence/` — **118 files / 4,771,139 bytes / 4.55 MiB**:

| group | files | bytes | what |
|---|---|---|---|
| `evidence/cost/` | 4 | 4,166,273 | the four recorded Developer trajectories the cost analysis reads |
| `evidence/observation/round4/deterministic/` | 37 | 222,299 | `.hoh/deterministic/**`: the step records and the verbatim payload behind each criterion |
| `evidence/observation/round4/round/` | 70 | 326,506 | `runs/bevy-round4/**`: the 57 raw MCP→BRP call files, the readings, the gate, the launch facts, the launch ledger |
| `evidence/observation/round4/iter-{1,2,3}/` | 6 | 53,776 | each iteration's `result.json` and the Tester's `evidence.json` |
| `evidence/observation/round4/meta.json` | 1 | 2,285 | the round's own meta |
| `evidence/index.json`, `evidence/README.md`, `evidence/tools/` | 3 | — | the index, the reader's guide and the two tools |

`evidence/index.json` carries 14 headline entries, each with its files and its command, and a
`not_reproducible_from_the_repository` list. The honest boundary is:

* **Reproducible from a clone** — the four trajectories' token totals and ratios; the corrected write
  profiles (directive calls, project calls, failed attempts, the write-free window); the withdrawn
  budget's K = 32 replay on all four recordings; the three band edges including the corrected
  **K ≥ 52**; the raw call files' shape; the Tester's own round-4 figures; and the coverage figure.
* **Not reproducible from a clone, and stated** — the provider's per-call usage for any call outside
  the four committed trajectories (and therefore every figure resting on the other rounds and roles);
  byte-level identity of what a successful shell write put on disk; whether the withdrawn budget or a
  tree-fingerprint signal behaves as projected on a live game; the four other round-4 attempts'
  workspace evidence, which the last pass overwrote; and the claim that this corpus is a faithful
  subset, which the copier's sha256 manifest supports but which can only be re-verified where the
  source still exists.

**A finding worth recording.** The trajectories have `.redacted.json` sidecars that are 187, 180, 180
and 977 bytes smaller than their raw siblings — the difference is twelve `<redacted>` replacements of
`HOH_ARTIFACT_DIR`, `HOH_GAME_ROUTE` and `HOH_HOH_BIN` **environment values**, not credentials. The
raw files are clean under the repository's own key-shape rule, so the raw files are what was committed
(the accounting reads the action text and the per-call usage; a redacted copy would be a different
input).

## 6. Defect D-1, restated

`LIVE-COST-REPORT.md` and `WRITE-ACCOUNTING-REPORT.md` both said "to cut no recorded work, **K ≥ 43**".
That is round-4 iteration 3's **directive** window. Under the corrected **project-write** accounting,
the live call's last directive write is call 43 and its **last project write is call 95**, so the rule
fires at call `44 + K`:

| K | abort call | what it does to the live call |
|---|---|---|
| 50 | 94 | cuts the call-95 `src\game.rs` write |
| **51** | **95** | **refuses that write itself** — the after-list is empty because the write never happens, which is why the strict `> abort` convention nearly hides it |
| **52** | **96** | cuts nothing recorded |

The **global floor is K ≥ 52** (K ≥ 51 under the replay's strict convention). The conclusion is
unchanged **and stronger**: `37 < 43 < 52`, so the bands still do not overlap and the lever is worse
than the report said. It is now pinned by
`tests/write_accounting.rs::the_global_safe_floor_is_fifty_two_and_not_forty_three`, and planted
against in P4.

## 7. Gate, plants, files

* **Gate**, in this batch's own build directory `F:/hof-cov-target`, with free space checked first
  (F: 66 G free) and no `cargo`/`rustc`/`hoh` process before or after: `cargo test --offline` →
  **literal exit code 0**, **800 passed / 0 failed / 6 ignored / 806 listed** over **60**
  `test result:` lines; `-- --list` exit 0 with 806 names; `-- --list --ignored` exit 0 with the same
  six real-engine tests; **0** `warning:` lines in stdout and stderr; `cargo fmt --all --check`
  exit **0** emitting **0 bytes**. The tree I started from measures **782 / 0 / 6 / 788** — so
  **18 tests added and 0 removed**, and the six ignored names are the same six.
* **Plants.** Four controlled plants, each green → red → green, each a single-occurrence literal edit,
  each restored **byte-exactly** (sha256 compared) with both mtimes set explicitly (`1791200000.0`
  for the plant, a newer `1791400000.0` for the restore, so cargo cannot skip the rebuild). Every
  green run exited **0**; every red run exited **101**, really ran (a `test result:` line and a panic
  site are in the log) and **named the intended test**:
  * **P1** — a surface whose battery step never ran is reported as **verified** (the RA-5 false-green).
  * **P2** — `FrameAdvance::verdict` ignores the frame advance, silently re-opening the S1 gap.
  * **P3** — `e3_process_liveness` is dropped from `E3_STEPS`, so `Q-startup`/`B2.1` name a step the
    battery does not run.
  * **P4** — the withdrawn budget's abort predicate becomes `>=`, moving the K ≥ 52 floor D-1 restates.

  Record: `F:/hof-cov-work/plants.json`, red logs `F:/hof-cov-work/PLANT-P*.log`.
* **Files.** Added `src/adapter/bevy/prd_surfaces.rs`, `tests/evidence_reproduction.rs`, `evidence/`
  and this report. Modified `battery.rs`, `round.rs`, `project.rs`, `adapter/mod.rs`, `bevy/mod.rs`,
  `model.rs`, `run_loop.rs`, `cli_impl.rs`, `src/prompts/skills/bevy-testing.md`, `tests/prd_coverage.rs`,
  `tests/write_accounting.rs`, and — **only where factually wrong** — `LIVE-COST-REPORT.md` and
  `WRITE-ACCOUNTING-REPORT.md` for D-1. `DECISIONS.md` gained **D305 by append only**
  (1,295,073 → 1,306,821 bytes; the old bytes are a byte prefix of the new file). The frozen documents
  — `REQUIREMENTS.md`, `PRD.md`, `DESIGN-OVERVIEW.md`, `DESIGN-DETAIL.md`, the spike reports, the batch
  reports and the acceptances — were **not touched**. No new dependency. No production call site
  enforces the coverage figure: it is published, not acted on.
* **Not committed, not pushed.** The working tree holds this batch's changes; the delegating agent
  commits and pushes. No `git add`, no `git commit`, no `git push` was run.

## 8. What worked, what does not, what I could not verify

**Worked.** The denominator is now a constant with a test that proves it does not move when the Tester
changes; every item carries its evidence or its reason; the two open gaps are decided — one closed by
an observation that uses nothing new, one named as unobservable with the reason and kept out of the
denominator. The cost analysis now runs from a clone: `tests/write_accounting.rs` prefers
`evidence/cost/`, and its numbers are the same numbers, because the committed files are byte-identical
to the recordings. The corrected global band floor is no longer a sentence in a report but a property
of the recording that four plants guard. D-1 is restated where it was wrong, and `DECISIONS.md` is
still append-only.

**Does not work — and this is the honest headline.** The cost criterion is still **not met**:
3,651,120 total tokens against 1,500,000, **2.434×**, on the one live Developer call, and the corrected
accounting makes the withdrawn lever's damage *larger*, not smaller. Nothing in this batch changes
that, and the `K ≥ 52` restatement makes it worse. Four of the 19 frozen surfaces will **never** be
verifiable by this harness — `C5`, `C6`, `Q-scale`, `Q-not-required` — so the ceiling is 15/19, and
that is a property of the PRD and of what an in-process observer can see, not a defect to be papered
over.

**Could not verify.** The new battery step has **never run against a real game**: no engine is
reachable offline, and this batch was instructed to run no round. Its unit surface, its fake-driver
phase, its persistence path and its failure shape are tested; the live path is not, and that is the
one thing about this batch that a green gate does not prove. I also did not re-derive the lever pairs
or the `compact_history` projections, and the corpus cannot be shown complete for a headline nobody
indexed.

## 9. The single most important thing for the next batch

**Run one live round on this tree and read `result.json.prd_coverage.surfaces`.** For the first time
the project has a coverage figure whose denominator is a constant and whose items name their own
evidence, so one round can be compared with the next. Expect **15/19 with four named unobservable
items**; if `Q-startup` or `B2.1` comes back red, the liveness step is measuring something real and
failing honestly — which is a better outcome than the assumption it replaced. And do not read `15/19`
as "five items short": four of the five are non-requirements or beyond an in-process observer's reach
**by design**, and the registry says so item by item. The fifth, `P3-goal-x`, is the one decision this
batch deliberately left to a human: closing it means adding a ninth reflectable surface, which is a
contract change, and that is a decision for whoever owns the frozen PRD — not for a subagent.
