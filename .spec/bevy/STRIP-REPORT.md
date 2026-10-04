```json
{
  "report": "STRIP-REPORT",
  "branch": "bevy-core",
  "date": "2026-10-04",
  "history": "master retains the full history and every removed file; nothing was copied into this branch to preserve it",
  "tracked_files": {
    "before": 7025,
    "after": 149,
    "removed": 6876
  },
  "removed_areas": [
    {
      "path": "godot-mcp/",
      "tracked_files": 6484,
      "reason": "the vendored Godot engine clone, its MCP module, the 20 test game projects, dist/, recovery/ and tools/; removed from the index and from disk"
    },
    {
      "path": ".spec/hof-rs/",
      "tracked_files": 350,
      "reason": "old-engine archaeology: REQUIREMENTS/DESIGN-OVERVIEW/DESIGN-DETAIL, PRD-mario.md, OBJECTIVE-COMPLETION.md and the ~330 task reports and acceptances"
    },
    {
      "path": ".spec/godot-mcp-engine/",
      "tracked_files": 1,
      "reason": "stub for the Godot engine module's spec, which lives in the fork repo"
    },
    {
      "path": "%DST%/",
      "tracked_files": 7,
      "reason": "TASK-085/086 cmd redirection residue (a directory literally named %DST%)"
    },
    {
      "path": "tests/",
      "tracked_files": 29,
      "reason": "15 test files that existed only to exercise the removed engine, plus 14 old-engine fixtures under tests/fixtures/dr58, dr76 and dr77"
    },
    {
      "path": "scripts/",
      "tracked_files": 3,
      "reason": "byte_claims.py and derive_dr76_fixtures.py (they only exist to write/derive the removed old-engine artifacts) and dr72-digest.ps1 (hard-codes runs/smoke-t6..t10)"
    },
    {
      "path": "src/adapter/godot.rs",
      "tracked_files": 1,
      "reason": "the legacy adapter module itself (7467 lines, 25 unit tests)"
    },
    {
      "path": "2609.01481v1.pdf_by_PaddleOCR-VL-1.6.md",
      "tracked_files": 1,
      "reason": "OCR of the research paper; the paper is not harness and not the Bevy flow"
    }
  ],
  "removed_from_worktree_only": [
    {
      "path": "godot-mcp/ (remaining ignored files)",
      "note": "664516 ignored/untracked files (~7.5 GB): the engine clone with its own .git, dist/exe and dist/*.zip, the archived exercise projects, recovery stashes"
    },
    {
      "path": "2609.01481v1.pdf",
      "bytes": 16004602,
      "note": "ignored, untracked"
    },
    {
      "path": "l.json",
      "bytes": 151,
      "note": "stray root JSON, untracked"
    },
    {
      "path": "p2.json",
      "bytes": 153,
      "note": "stray root JSON, untracked"
    },
    {
      "path": "pv.json",
      "bytes": 62,
      "note": "stray root JSON, untracked"
    },
    {
      "path": "r.json",
      "bytes": 153,
      "note": "stray root JSON, untracked"
    }
  ],
  "code_changes": [
    {
      "path": "src/adapter/godot.rs",
      "kind": "deleted",
      "reason": "the legacy adapter: GodotAdapter (ProjectAdapter + the honest-failure GameAdapter impl), the seven-step Godot battery, the scene validator and its tests"
    },
    {
      "path": "src/adapter/mod.rs",
      "kind": "modified",
      "reason": "dropped `pub mod godot` / `pub use godot::GodotAdapter`; dropped the now unconstructed EngineId::Godot48Legacy variant; de-Godoted the doc comments"
    },
    {
      "path": "src/adapter/engine.rs",
      "kind": "modified",
      "reason": "the `no engine binary` reason no longer names the removed `adapter.godot.editor_binary` configuration key"
    },
    {
      "path": "src/config.rs",
      "kind": "modified",
      "reason": "removed GodotConfig (editor_binary/cache_excludes/main_scene) and AdapterConfig.godot; AdapterConfig is now just the adapter kind"
    },
    {
      "path": "src/cli.rs",
      "kind": "modified",
      "reason": "`--adapter` default `godot` -> `test` (the only remaining ProjectAdapter kind); removed Godot wording from the doc comments"
    },
    {
      "path": "src/cli_impl.rs",
      "kind": "modified",
      "reason": "dropped the godot/godot_mcp branch of build_adapter_kind, the Godot editor-scope unit test, the `.spec/hof-rs/PRD-mario.md` default spec path (now `.spec/bevy/PRD.md`) and rollback's Godot cache-exclude source (now the runtime's always-excluded pair)"
    },
    {
      "path": "src/runtime/run_loop.rs",
      "kind": "modified",
      "reason": "removed note_mcp_desync and its two call sites: the sync report it read was written by the removed engine's MCP server, so the wiring had no producer left"
    },
    {
      "path": "src/runtime/view.rs",
      "kind": "modified",
      "reason": "the DR-49/DR-62 supersession producer it names is now runtime::hygiene::invalidate_artifact (doc comment + test call)"
    },
    {
      "path": "src/runtime/hygiene.rs",
      "kind": "modified",
      "reason": "received the engine-neutral DR-49/DR-62 producer out of the deleted module (ArtifactFingerprint, artifact_fingerprint, artifact_is_fresh, invalidate_artifact) together with its two tests, next to stale_name and SupersededSet"
    },
    {
      "path": "config/hoh.yaml",
      "kind": "modified",
      "reason": "`adapter.kind: test`, the adapter.godot block (its editor_binary pointed into the deleted tree) removed, runtime.spec -> .spec/bevy/PRD.md"
    },
    {
      "path": ".gitattributes",
      "kind": "modified",
      "reason": "dropped the byte pins for the removed trees (tests/fixtures/dr58, tests/fixtures/dr76, .spec/hof-rs/tasks/TASK-SMOKE-T9-evidence); kept the .githooks/**, scripts/*.sh and .spec/bevy/PRD.md pins"
    },
    {
      "path": ".gitignore",
      "kind": "modified",
      "reason": "dropped ~200 lines of godot-mcp / recovery / %DST% / PDF archaeology; kept secrets, .workspace/, runs/, target/ and editor/OS rules; nothing was added"
    }
  ],
  "deleted_tests": {
    "files": [
      {
        "path": "tests/append_only_guard.rs",
        "test_functions": 13,
        "justification": "pins byte prefixes of four reports under .spec/hof-rs/tasks/**; its fixtures are removed by this branch"
      },
      {
        "path": "tests/byte_claims.rs",
        "test_functions": 4,
        "justification": "recomputes the DR-71 byte-claim blocks inside three .spec/hof-rs/tasks/** documents (and needs their historical git blobs)"
      },
      {
        "path": "tests/cli_init.rs",
        "test_functions": 5,
        "justification": "drives `hoh init` against the Godot A0 scaffold (project.godot, the bundled addon, [editor_plugins]); only GodotAdapter::initialize ever produced that scaffold"
      },
      {
        "path": "tests/dr58_payload_shapes.rs",
        "test_functions": 5,
        "justification": "Godot MCP reply shapes frozen from smoke-t7; the dr58 fixtures are removed"
      },
      {
        "path": "tests/dr76_payload_shapes.rs",
        "test_functions": 5,
        "justification": "Godot interaction fixtures derived from runs/smoke-t10 via the removed derivation script; uses godot::hud_label_candidates"
      },
      {
        "path": "tests/dr77_evidence_tightening.rs",
        "test_functions": 6,
        "justification": "pins quotations in .spec/hof-rs/tasks/TASK-DR73-REPORT.md plus the dr77 fixtures, both removed"
      },
      {
        "path": "tests/dual_endpoint.rs",
        "test_functions": 8,
        "justification": "Godot's two MCP endpoints: the editor endpoint (9877) and the port editor_play_scene announces"
      },
      {
        "path": "tests/evidence_battery.rs",
        "test_functions": 74,
        "justification": "the Godot seven-step battery and its interaction windows, driven through GodotAdapter and the dr58/dr76/dr77 fixtures"
      },
      {
        "path": "tests/frozen_evidence.rs",
        "test_functions": 6,
        "justification": "reads the frozen smoke-t9 command dump under .spec/hof-rs/tasks/**"
      },
      {
        "path": "tests/godot_smoke.rs",
        "test_functions": 7,
        "justification": "real Godot smoke; also loads .spec/hof-rs/PRD-mario.md"
      },
      {
        "path": "tests/interaction_contract.rs",
        "test_functions": 6,
        "justification": "Godot interaction semantics, and it scans the removed src/adapter/godot.rs as its source of truth"
      },
      {
        "path": "tests/launchable_gate.rs",
        "test_functions": 23,
        "justification": "the DR-24 gate driven through the real GodotAdapter battery and godot::validate_scene_structure"
      },
      {
        "path": "tests/round_artifacts_sidecar.rs",
        "test_functions": 2,
        "justification": "pins .spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/** and its generated sidecar"
      },
      {
        "path": "tests/round_game_start.rs",
        "test_functions": 6,
        "justification": "GodotAdapter::start_round_game's publish ordering; the runtime half of that contract is still covered by tests/round_game_window.rs (FakeAdapter + RoundGameStub)"
      },
      {
        "path": "tests/start_state.rs",
        "test_functions": 8,
        "justification": "the Godot .godot/ cache rebuild behaviour of A0"
      }
    ],
    "test_functions_in_deleted_files": 178,
    "in_file_deletions": [
      {
        "where": "src/adapter/godot.rs (whole module)",
        "test_functions": 25,
        "justification": "all of them exercised the removed adapter"
      },
      {
        "where": "src/cli_impl.rs: doctor_report_contains_the_editor_scope_confirmation",
        "test_functions": 1,
        "justification": "built a GodotAdapter to read its godot.editor_scope doctor item"
      },
      {
        "where": "tests/bevy_adapter_b1.rs: the_legacy_godot_adapter_implements_the_capability_surface_without_panicking",
        "test_functions": 1,
        "justification": "the trait-contract half is already covered by the Bevy adapter and by src/adapter/mod.rs's own tests"
      },
      {
        "where": "tests/mcp_desync.rs: 5 tests",
        "test_functions": 5,
        "justification": "the battery/session-sync ones (a_battery_step_never_reports_a_mis_correlated_payload_as_success, every_battery_raw_payload_records_the_jsonrpc_correlation, a_desynchronized_session_is_reported_in_result_json_warnings, a_healthy_session_records_no_desync_warning, the_monitor_reply_helper_covers_both_actions); the four pure-harness DR-29 re-correlation tests were kept"
      },
      {
        "where": "tests/tool_discovery.rs: the_godot_dev_skeleton_is_a_valid_scene",
        "test_functions": 1,
        "justification": "validated the godot-dev skill's scene skeleton with godot::validate_scene_structure"
      },
      {
        "where": "tests/wrap_up_budget.rs: the_godot_developer_artifact_validity_needs_a_real_entry_script",
        "test_functions": 1,
        "justification": "unit-tested GodotAdapter::developer_artifact_valid; the DR-37 wrap-up behaviour itself is still covered by the same file through FakeAdapter"
      },
      {
        "where": "tests/write_integrity.rs: the_production_adapter_names_the_fragment_and_the_foreign_escape",
        "test_functions": 1,
        "justification": "unit-tested godot::developer_artifact_defects_in"
      },
      {
        "where": "tests/game_route_across_processes.rs: 3 role-started-scene tests",
        "test_functions": 3,
        "justification": "a_role_started_scene_republishes_the_game_route_for_later_processes, a_role_started_scene_that_never_becomes_ready_is_refused_and_leaves_no_route, a_role_started_scene_whose_route_cannot_be_published_fails_loudly; the publisher they drove was GodotAdapter::publish_role_started_game_route"
      }
    ],
    "test_functions_deleted_in_kept_files": 13,
    "tests_moved_from_the_deleted_module_and_kept": 2,
    "deleted_fixtures": [
      "tests/fixtures/dr58/** (8 files)",
      "tests/fixtures/dr76/** (4 files)",
      "tests/fixtures/dr77/** (2 files)"
    ],
    "kept_and_adapted": [
      "tests/e1_increment.rs: the exclusion set is now derived from TestAdapter (the adapter the runtime is wired to) instead of config.adapter.godot",
      "tests/result_semantics.rs: the dead-project gate is now driven by FakeAdapter's with_gate_failure instead of a GodotAdapter battery",
      "tests/role_shell_contract.rs: the evidence playbook comes from TestAdapter",
      "tests/prompt_shell_contract.rs: the scratch-discipline assertion uses HashExcludes's always-excluded pair (no Godot cache list to read)",
      "tests/round_game_window.rs: only stale references to the removed module in prose",
      "tests/bevy_adapter_b1.rs, tests/tool_discovery.rs, tests/write_integrity.rs, tests/wrap_up_budget.rs, tests/mcp_desync.rs, tests/game_route_across_processes.rs: the remaining tests in these files are unchanged in substance"
    ]
  },
  "gate": {
    "cargo_test": {
      "command": "cargo test --offline",
      "exit_code": 0,
      "passed": 625,
      "failed": 0,
      "ignored": 2,
      "measured": 0,
      "filtered_out": 0,
      "test_targets_listed": 48,
      "doc_test_targets_listed": 1,
      "warnings": 0,
      "dead_code_warnings": 0,
      "second_test_process_running": false,
      "build_dir": "F:/moonbit-hof-rs-build/target (outside the repository)"
    },
    "cargo_fmt": {
      "command": "cargo fmt --all --check",
      "exit_code": 0,
      "output_bytes": 0
    },
    "clean_rebuild_check": {
      "command": "cargo test --offline --no-run (after `cargo clean -p hof-rs`)",
      "exit_code": 0,
      "warnings": 0,
      "note": "all 48 test executables and the lib were rebuilt from clean crate artifacts so the zero-dead-code-warning claim is not an incremental artefact"
    }
  },
  "left_in_tree_not_core": [
    "src/adapter/engine.rs keeps the DR-44 engine-identity probe with its `godot.engine_binary` / `godot.engine_version` doctor item names and ENGINE_KIND_GODOT fallback. The probe, the engine_identity gate step and the meta.json.engine evidence block are harness machinery (the acceptance gate must survive), but no adapter declares a binary any more, so the Godot naming is dead weight.",
    "src/prompts/skills/godot-dev.md and godot-testing.md (and the Godot sections of developer.md/planner.md/tester.md) stay. Removing them would have deleted engine-neutral prompt-discipline tests (scratch discipline, the completion protocol, the tool index, the delivered-materials checks) in five files, which instruction 7 says to keep. They are old-engine prompt content and the first thing a Bevy skill batch should replace.",
    "src/runtime/project_map.rs treats `project.godot`, `*.tscn`, `*.gd` and ADDON_MISSING.txt as key files; that rule is Godot-shaped and is pinned by tests/tool_discovery.rs.",
    "src/runtime/hygiene.rs still lists `.godot` and `.import` in the hygiene ignore set, and run_loop.rs's `no_engineering_write` message still names `.godot/**`/`.import/**`.",
    "tests/fixtures/mcp/** keeps the embedded 177-tool Godot vocabulary (src/tools/index.rs includes tests/fixtures/mcp/tools_list.json); it is the harness's tool-index source and four tool-surface tests pin it, but it is the old engine's contract.",
    "The tool channel keeps its DR-29 session-sync probe (ToolChannel::session_sync_probe, McpClient::session_sync_probe, SessionSyncReport). Its only caller was the removed adapter, so it is now unexercised production API.",
    ".githooks/README.md and scripts/accept-commit.sh still quote `.spec/hof-rs/tasks/TASK-XX-ACCEPTANCE.md` as an example acceptance path in help/error text. The gate itself is untouched; the example path is stale.",
    ".workspace/ (mario, fresh-t11..t16) is the configured runtime workspace and is full of Godot projects; it is ignored/untracked and was left in place so `hoh run` still has a workspace. runs/** was not written to and was left entirely alone. target/ was left in place (the gate used an external build directory).",
    ".spec/bevy/BATCH-B3-ACCEPTANCE.md is untracked and appeared inside .spec/bevy/ during this session; it is not mine and I did not touch .spec/bevy/**."
  ]
}
```

# STRIP-REPORT — `bevy-core` keeps the harness and the Bevy development flow only

- Branch: **`bevy-core`**, created from the tip and checked out. **`master` retains the full
  history and every removed file** — nothing was lost by this strip, and nothing was copied
  into this branch to preserve it.
- What was asked: keep the harness (CLI, runtime, policy and integrity checks, tool channel,
  acceptance gate and its ledger) and the Bevy flow (`GameAdapter` trait, `BevyAdapter`, the
  MCP tool surface, the Bevy battery, the round-evidence layout, `.spec/bevy/**`), and remove
  the abandoned Godot engine and everything that only served it.

## 1. Counts

| measure | value |
|---|---|
| tracked files before | 7025 |
| tracked files after | 149 |
| tracked files removed | 6876 |
| test functions removed with the 15 deleted test files | 178 |
| test functions deleted inside kept files | 13 |
| unit tests removed with `src/adapter/godot.rs` | 25 |
| tests moved out of the deleted module and kept | 2 |
| ignored/untracked files also removed from the worktree | 664,521 files: 5 root strays totalling 16,005,121 B, plus 664,516 files (~7.5 GB) under `godot-mcp/` |

## 2. Per area

| area | tracked files removed | what it was |
|---|---|---|
| `godot-mcp/` | 6484 | the vendored Godot engine clone, its MCP module, the 20 test game projects, dist/, recovery/ and tools/; removed from the index and from disk |
| `.spec/hof-rs/` | 350 | old-engine archaeology: REQUIREMENTS/DESIGN-OVERVIEW/DESIGN-DETAIL, PRD-mario.md, OBJECTIVE-COMPLETION.md and the ~330 task reports and acceptances |
| `.spec/godot-mcp-engine/` | 1 | stub for the Godot engine module's spec, which lives in the fork repo |
| `%DST%/` | 7 | TASK-085/086 cmd redirection residue (a directory literally named %DST%) |
| `tests/` | 29 | 15 test files that existed only to exercise the removed engine, plus 14 old-engine fixtures under tests/fixtures/dr58, dr76 and dr77 |
| `scripts/` | 3 | byte_claims.py and derive_dr76_fixtures.py (they only exist to write/derive the removed old-engine artifacts) and dr72-digest.ps1 (hard-codes runs/smoke-t6..t10) |
| `src/adapter/godot.rs` | 1 | the legacy adapter module itself (7467 lines, 25 unit tests) |
| `2609.01481v1.pdf_by_PaddleOCR-VL-1.6.md` | 1 | OCR of the research paper; the paper is not harness and not the Bevy flow |

The `godot-mcp/` directory was also cleared from disk: after the 6484 tracked files were
removed from the index, 664,516 ignored/untracked files remained (the engine clone with its
own `.git`, `dist/exe`, `dist/*.zip`, the archived exercise projects, the `recovery/`
stashes). Removing them needed one destructive step that should be on the record: the
leftover **Godot editor process (pid 3940)** had
`godot-mcp/godot/bin/godot.windows.editor.x86_64.mono.exe` open, so the first pass failed
with `WinError 5`; I stopped that process and the second pass completed. Nothing else under
the repository was held open.

Worktree-only (untracked/ignored, deleted and named here as the task allows): the paper PDF
`2609.01481v1.pdf` (16,004,602 B), the four loose root JSON files
(`l.json` 151 B, `p2.json` 153 B, `pv.json` 62 B, `r.json` 153 B) and the `godot-mcp/`
residue above. Every deletion of a directory went through a
print-then-verify-then-remove Python helper outside the repository; no `rm -rf` was used and
no `git checkout --` was used. Tracked files went through `git rm`.

## 3. Code changes (deleted or changed, with the reason)

| file | change | reason |
|---|---|---|
| `src/adapter/godot.rs` | deleted | the legacy adapter: GodotAdapter (ProjectAdapter + the honest-failure GameAdapter impl), the seven-step Godot battery, the scene validator and its tests |
| `src/adapter/mod.rs` | modified | dropped `pub mod godot` / `pub use godot::GodotAdapter`; dropped the now unconstructed EngineId::Godot48Legacy variant; de-Godoted the doc comments |
| `src/adapter/engine.rs` | modified | the `no engine binary` reason no longer names the removed `adapter.godot.editor_binary` configuration key |
| `src/config.rs` | modified | removed GodotConfig (editor_binary/cache_excludes/main_scene) and AdapterConfig.godot; AdapterConfig is now just the adapter kind |
| `src/cli.rs` | modified | `--adapter` default `godot` -> `test` (the only remaining ProjectAdapter kind); removed Godot wording from the doc comments |
| `src/cli_impl.rs` | modified | dropped the godot/godot_mcp branch of build_adapter_kind, the Godot editor-scope unit test, the `.spec/hof-rs/PRD-mario.md` default spec path (now `.spec/bevy/PRD.md`) and rollback's Godot cache-exclude source (now the runtime's always-excluded pair) |
| `src/runtime/run_loop.rs` | modified | removed note_mcp_desync and its two call sites: the sync report it read was written by the removed engine's MCP server, so the wiring had no producer left |
| `src/runtime/view.rs` | modified | the DR-49/DR-62 supersession producer it names is now runtime::hygiene::invalidate_artifact (doc comment + test call) |
| `src/runtime/hygiene.rs` | modified | received the engine-neutral DR-49/DR-62 producer out of the deleted module (ArtifactFingerprint, artifact_fingerprint, artifact_is_fresh, invalidate_artifact) together with its two tests, next to stale_name and SupersededSet |
| `config/hoh.yaml` | modified | `adapter.kind: test`, the adapter.godot block (its editor_binary pointed into the deleted tree) removed, runtime.spec -> .spec/bevy/PRD.md |
| `.gitattributes` | modified | dropped the byte pins for the removed trees (tests/fixtures/dr58, tests/fixtures/dr76, .spec/hof-rs/tasks/TASK-SMOKE-T9-evidence); kept the .githooks/**, scripts/*.sh and .spec/bevy/PRD.md pins |
| `.gitignore` | modified | dropped ~200 lines of godot-mcp / recovery / %DST% / PDF archaeology; kept secrets, .workspace/, runs/, target/ and editor/OS rules; nothing was added |

Two refusals worth stating, because they are the difference between "the suite still passes"
and "the suite still means something":

- **`src/runtime/hygiene.rs` gained code instead of losing it.** `ArtifactFingerprint`,
  `artifact_fingerprint`, `artifact_is_fresh` and `invalidate_artifact` are the DR-49/DR-62
  *producer* half of the supersession contract whose *consumer* (`SupersededSet`,
  `view::copy_evidence`) is production harness code. They happened to live in the Godot
  module because a screenshot was the only file artifact; they are engine-neutral, so they
  moved next to `stale_name`/`SupersededSet` with their two tests rather than being deleted
  with the module.
- **`src/tools/**` was left alone.** `src/tools/mod.rs`'s DR-29 session-sync probe and
  `SessionSyncReport` have no caller left, but they are the harness's own JSON-RPC
  correlation surface; deleting them would have been a harness change, not a Godot removal.
  They are listed as residue in §6.

## 4. Deleted tests

### 4.1 Whole files (178 test functions)

| test file | tests | why it cannot survive |
|---|---|---|
| `tests/append_only_guard.rs` | 13 | pins byte prefixes of four reports under .spec/hof-rs/tasks/**; its fixtures are removed by this branch |
| `tests/byte_claims.rs` | 4 | recomputes the DR-71 byte-claim blocks inside three .spec/hof-rs/tasks/** documents (and needs their historical git blobs) |
| `tests/cli_init.rs` | 5 | drives `hoh init` against the Godot A0 scaffold (project.godot, the bundled addon, [editor_plugins]); only GodotAdapter::initialize ever produced that scaffold |
| `tests/dr58_payload_shapes.rs` | 5 | Godot MCP reply shapes frozen from smoke-t7; the dr58 fixtures are removed |
| `tests/dr76_payload_shapes.rs` | 5 | Godot interaction fixtures derived from runs/smoke-t10 via the removed derivation script; uses godot::hud_label_candidates |
| `tests/dr77_evidence_tightening.rs` | 6 | pins quotations in .spec/hof-rs/tasks/TASK-DR73-REPORT.md plus the dr77 fixtures, both removed |
| `tests/dual_endpoint.rs` | 8 | Godot's two MCP endpoints: the editor endpoint (9877) and the port editor_play_scene announces |
| `tests/evidence_battery.rs` | 74 | the Godot seven-step battery and its interaction windows, driven through GodotAdapter and the dr58/dr76/dr77 fixtures |
| `tests/frozen_evidence.rs` | 6 | reads the frozen smoke-t9 command dump under .spec/hof-rs/tasks/** |
| `tests/godot_smoke.rs` | 7 | real Godot smoke; also loads .spec/hof-rs/PRD-mario.md |
| `tests/interaction_contract.rs` | 6 | Godot interaction semantics, and it scans the removed src/adapter/godot.rs as its source of truth |
| `tests/launchable_gate.rs` | 23 | the DR-24 gate driven through the real GodotAdapter battery and godot::validate_scene_structure |
| `tests/round_artifacts_sidecar.rs` | 2 | pins .spec/hof-rs/tasks/TASK-SMOKE-T10-evidence/** and its generated sidecar |
| `tests/round_game_start.rs` | 6 | GodotAdapter::start_round_game's publish ordering; the runtime half of that contract is still covered by tests/round_game_window.rs (FakeAdapter + RoundGameStub) |
| `tests/start_state.rs` | 8 | the Godot .godot/ cache rebuild behaviour of A0 |

Fixtures deleted with them: `tests/fixtures/dr58/**` (8 files), `tests/fixtures/dr76/**`
(4 files), `tests/fixtures/dr77/**` (2 files). `tests/fixtures/mcp/**` was **kept**: the
harness embeds it (`src/tools/index.rs`), and four surviving tool-surface tests pin it.

### 4.2 Inside kept files (13 test functions + the 25 of the deleted module)

| where | tests | why |
|---|---|---|
| src/adapter/godot.rs (whole module) | 25 | all of them exercised the removed adapter |
| src/cli_impl.rs: doctor_report_contains_the_editor_scope_confirmation | 1 | built a GodotAdapter to read its godot.editor_scope doctor item |
| tests/bevy_adapter_b1.rs: the_legacy_godot_adapter_implements_the_capability_surface_without_panicking | 1 | the trait-contract half is already covered by the Bevy adapter and by src/adapter/mod.rs's own tests |
| tests/mcp_desync.rs: 5 tests | 5 | the battery/session-sync ones (a_battery_step_never_reports_a_mis_correlated_payload_as_success, every_battery_raw_payload_records_the_jsonrpc_correlation, a_desynchronized_session_is_reported_in_result_json_warnings, a_healthy_session_records_no_desync_warning, the_monitor_reply_helper_covers_both_actions); the four pure-harness DR-29 re-correlation tests were kept |
| tests/tool_discovery.rs: the_godot_dev_skeleton_is_a_valid_scene | 1 | validated the godot-dev skill's scene skeleton with godot::validate_scene_structure |
| tests/wrap_up_budget.rs: the_godot_developer_artifact_validity_needs_a_real_entry_script | 1 | unit-tested GodotAdapter::developer_artifact_valid; the DR-37 wrap-up behaviour itself is still covered by the same file through FakeAdapter |
| tests/write_integrity.rs: the_production_adapter_names_the_fragment_and_the_foreign_escape | 1 | unit-tested godot::developer_artifact_defects_in |
| tests/game_route_across_processes.rs: 3 role-started-scene tests | 3 | a_role_started_scene_republishes_the_game_route_for_later_processes, a_role_started_scene_that_never_becomes_ready_is_refused_and_leaves_no_route, a_role_started_scene_whose_route_cannot_be_published_fails_loudly; the publisher they drove was GodotAdapter::publish_role_started_game_route |

### 4.3 Kept, and how they were adapted

- tests/e1_increment.rs: the exclusion set is now derived from TestAdapter (the adapter the runtime is wired to) instead of config.adapter.godot
- tests/result_semantics.rs: the dead-project gate is now driven by FakeAdapter's with_gate_failure instead of a GodotAdapter battery
- tests/role_shell_contract.rs: the evidence playbook comes from TestAdapter
- tests/prompt_shell_contract.rs: the scratch-discipline assertion uses HashExcludes's always-excluded pair (no Godot cache list to read)
- tests/round_game_window.rs: only stale references to the removed module in prose
- tests/bevy_adapter_b1.rs, tests/tool_discovery.rs, tests/write_integrity.rs, tests/wrap_up_budget.rs, tests/mcp_desync.rs, tests/game_route_across_processes.rs: the remaining tests in these files are unchanged in substance

The four pure-harness DR-29 re-correlation tests in `tests/mcp_desync.rs`
(`a_correct_server_needs_zero_probes`, `a_lagging_server_is_re_correlated`,
`a_persistently_desynced_server_returns_a_typed_error`,
`a_mis_correlated_payload_of_another_shape_is_never_used`) were kept, together with the
programmable fake HTTP server they drive; only the Godot-battery half of that file went. The
`unwrap_mcp_payload` helper they used lived in the deleted module, so a 15-line local copy
replaced it.

## 5. Gate evidence

| gate | result |
|---|---|
| `cargo test --offline` | **exit code 0** — 625 passed, 0 failed, 2 ignored, 0 measured, 0 filtered out, across 48 test targets + 1 doc-test target |
| `cargo fmt --all --check` | **exit code 0** (no output) |
| clean-crate rebuild, `cargo test --offline --no-run` after `cargo clean -p hof-rs` | **exit code 0**, **0 warnings**, 0 `dead_code` diagnostics — a clean rebuild was used so that "zero dead-code warnings" is not an incremental-build artefact |

Both gate commands were run with `CARGO_TARGET_DIR=F:/moonbit-hof-rs-build/target`, i.e. a
build directory of the task's own **outside the repository**, and the second gate command was
run after the test process had exited, so no second test process was running when either was
measured. Nothing under `runs/**` was written (7341 files, 0 modified today). The two ignored
tests are the pre-existing `#[ignore]`d real-Bevy smoke tests in `tests/bevy_adapter_b1.rs`
and `tests/bevy_adapter_b2.rs`; no test was newly ignored.

## 6. What is still in the tree and still not core

1. src/adapter/engine.rs keeps the DR-44 engine-identity probe with its `godot.engine_binary` / `godot.engine_version` doctor item names and ENGINE_KIND_GODOT fallback. The probe, the engine_identity gate step and the meta.json.engine evidence block are harness machinery (the acceptance gate must survive), but no adapter declares a binary any more, so the Godot naming is dead weight.
2. src/prompts/skills/godot-dev.md and godot-testing.md (and the Godot sections of developer.md/planner.md/tester.md) stay. Removing them would have deleted engine-neutral prompt-discipline tests (scratch discipline, the completion protocol, the tool index, the delivered-materials checks) in five files, which instruction 7 says to keep. They are old-engine prompt content and the first thing a Bevy skill batch should replace.
3. src/runtime/project_map.rs treats `project.godot`, `*.tscn`, `*.gd` and ADDON_MISSING.txt as key files; that rule is Godot-shaped and is pinned by tests/tool_discovery.rs.
4. src/runtime/hygiene.rs still lists `.godot` and `.import` in the hygiene ignore set, and run_loop.rs's `no_engineering_write` message still names `.godot/**`/`.import/**`.
5. tests/fixtures/mcp/** keeps the embedded 177-tool Godot vocabulary (src/tools/index.rs includes tests/fixtures/mcp/tools_list.json); it is the harness's tool-index source and four tool-surface tests pin it, but it is the old engine's contract.
6. The tool channel keeps its DR-29 session-sync probe (ToolChannel::session_sync_probe, McpClient::session_sync_probe, SessionSyncReport). Its only caller was the removed adapter, so it is now unexercised production API.
7. .githooks/README.md and scripts/accept-commit.sh still quote `.spec/hof-rs/tasks/TASK-XX-ACCEPTANCE.md` as an example acceptance path in help/error text. The gate itself is untouched; the example path is stale.
8. .workspace/ (mario, fresh-t11..t16) is the configured runtime workspace and is full of Godot projects; it is ignored/untracked and was left in place so `hoh run` still has a workspace. runs/** was not written to and was left entirely alone. target/ was left in place (the gate used an external build directory).
9. .spec/bevy/BATCH-B3-ACCEPTANCE.md is untracked and appeared inside .spec/bevy/ during this session; it is not mine and I did not touch .spec/bevy/**.

## 7. What a Bevy round still needs

Removing the Godot adapter leaves the `ProjectAdapter` slot with only the offline
`TestAdapter`, so `config/hoh.yaml` ships `adapter.kind: test` and `--adapter` defaults to
`test`. `BevyAdapter` is a `GameAdapter` (build, launch, semantic reads, injections, battery)
and is not yet a `ProjectAdapter`, and nothing implements
`publish_role_started_game_route` any more. Those gaps are the real end-to-end round's work,
not archaeology: they are listed here so the next batch starts from a green, honest tree
instead of from a tree that still carries the old engine.
