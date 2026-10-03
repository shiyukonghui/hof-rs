# BATCH-B3 REPORT — twelve inherited defects, the real build path, the pinned timing repair

- 日期 / Date: 2026-10-05
- 执行者 / Executor: implementation subagent (no prior context; the task prompt and the documents it named were authoritative)
- 上游 / Upstream, read in order: `.spec/bevy/BATCH-B2-ACCEPTANCE.md` (the work list),
  `.spec/bevy/DESIGN-DETAIL.md`, `.spec/bevy/REQUIREMENTS.md`, `.spec/bevy/PRD.md`,
  `.spec/bevy/DESIGN-OVERVIEW.md`, `.spec/bevy/BATCH-B1-REPORT.md`,
  `.spec/bevy/BATCH-B1-ACCEPTANCE.md`, `DECISIONS.md` D296/D297, and the code under
  `src/adapter/**` and `tests/`.
- 交付物 / Deliverables: **this file**, plus `.spec/bevy/BATCH-B2-RECONSTRUCTION.md`
  (B2-3's second half: B2's missing report reconstructed from the diff).
- Environment: offline; no engine, no game, no network. Scratch, logs, backups and copies under
  `F:/b3-scratch/` (outside the repository). Never `rm -rf`; every removal used Python's
  remove-tree on a printed, verified path inside `F:/b3-scratch`. Never `git checkout --`.
  Nothing under `runs/**` was written. Nothing was pushed.

```json
{
  "verdict": "pass-with-declared-gaps",
  "batch": "BATCH-B3",
  "defects_worked": 12,
  "defects_fixed": 12,
  "defects_declared_unfixed": 0,
  "environment": "offline, no engine, no game, no network; scratch F:/b3-scratch; CARGO_TARGET_DIR=F:/b3-scratch/target-base for the baseline and F:/b3-scratch/target-dev for the final revision",
  "baseline_revision": "the pre-B3 working tree (B2 as landed on fca7647), restored in place from a sha256-verified backup for the measurement",
  "baseline_gate": {
    "command": "cargo test --offline",
    "literal_exit_code": 0,
    "passed": 814,
    "failed": 0,
    "ignored": 9,
    "listed": 823,
    "result_lines": 64,
    "dead_code_warnings": 1
  },
  "final_gate": {
    "command": "cargo test --offline",
    "literal_exit_code": 0,
    "passed": 832,
    "failed": 0,
    "ignored": 9,
    "listed": 841,
    "result_lines": 64,
    "dead_code_warnings": 0,
    "taken": "on the final source revision before a layout-only cargo fmt pass; the post-fmt tree differs from it by whitespace, commas and two closure braces only (character-level diff of build.rs/contract.rs/tests/bevy_adapter_b2.rs)"
  },
  "fmt_gate": {
    "before": {
      "command": "cargo fmt --all --check",
      "literal_exit_code": 1,
      "violations": "4 hunks, all line-wrapping, in src/adapter/bevy/battery.rs"
    },
    "after_layout_only_fmt": {
      "command": "cargo fmt --all --check",
      "literal_exit_code": 0
    }
  },
  "forced_rebuild": {
    "done": false,
    "reason": "the dispatcher stopped further builds before this step; cleared fingerprints plus touching every tracked .rs file and rerunning the gate was not performed"
  },
  "test_delta": {
    "passed": 18,
    "ignored": 0,
    "removed": 0,
    "renamed": 1,
    "dead_code_warnings_removed": 1
  },
  "hashes": {
    "contract_sha256": {
      "old_b1": "4af153e77af87ceddb162c4b782701ee0b6c066a651d4e4b5d1e71f329649c69",
      "current_b2_b3": "792001e7e629ccc25d6c486eeb54360d83ffb208befa4ca5e430c6f0e747f4f9",
      "moved_by_b3": false
    },
    "tool_list_sha256": {
      "old_b1": "e177325fe8b2036c355d37b9373b85b524f4a7f0d999e087711366bca661ae97",
      "current_b2_b3": "bcf03c0b06295cfd27cc0359a7fa272ed435bdf61525d67b08981c62d30e43b1",
      "moved_by_b3": false
    },
    "feature_set_sha256": {
      "old_b1": "d6a90ba39e67b9e05fd28d97cc570dc989a03e8ec7a15ba93d077d5fe95d1f96",
      "current_b2_b3": "d6a90ba39e67b9e05fd28d97cc570dc989a03e8ec7a15ba93d077d5fe95d1f96",
      "moved_by_b3": false
    }
  },
  "changed_files": {
    ".spec/bevy/BATCH-B2-RECONSTRUCTION.md": "new",
    ".spec/bevy/BATCH-B3-REPORT.md": "new",
    "src/adapter/bevy/battery.rs": "8d657f5752c90b86982eddf4bbe154f4c10a2196a603840401d0b5899e201eb7",
    "src/adapter/bevy/brp.rs": "84dcabf9f600dc63a4fe4a0fd3e6b9affca03f9e796c84a14835f7038d310b8d",
    "src/adapter/bevy/build.rs": "0f5c652416890ae761bd6a77adac943bfe45d9104f40540b8e28c6a6a26dd37c",
    "src/adapter/bevy/contract.rs": "9349b6e716233e95fd6bd1dfade2418f617452e20f797949249673d95b1f0bf7",
    "src/adapter/bevy/launch.rs": "8a93f7e88b26bca5b481c8fc21d810a7bb30467231a67711467b4739dd4aa8eb",
    "src/adapter/bevy/mod.rs": "20a851df8a6b3fae2ac41cf7f6c30e626b91e4675dbe684c4e0fda9a4fc432bc",
    "src/adapter/mcp/server.rs": "00ca85fe0dce54f3bed68dc7455823febdfefd60402827e4513932d79c6786f7",
    "src/adapter/mod.rs": "8c009f7a475c6b9891df9cff71fcf2686fdc9ea7ac8065416aeb72a936d7b29b",
    "tests/bevy_adapter_b2.rs": "247d8703df1500a02ba89d209e3a6fc37dc2aa73a9bb5448df7a6a59ee083944"
  },
  "plants": [
    {
      "id": "P_B2_1",
      "file": "src/adapter/bevy/build.rs",
      "edit": "the source contract reader's register_type filter forced to false",
      "named_test": "adapter::bevy::tests::a_real_project_reaches_the_build_and_the_contract_check_with_coherent_reasons",
      "red": true,
      "restore_sha256": "7381b734a67f1a8107e1861f8ba9c2d625c24cd1dc9f4e40353d51cfcd0dc1e7",
      "green_after_restore": true
    },
    {
      "id": "P_B2_2",
      "file": "src/adapter/bevy/brp.rs",
      "edit": "the set_nonblocking(false) restore and its counter removed from the in-process fake",
      "named_test": "adapter::bevy::brp::tests::the_fake_restores_blocking_on_every_accepted_stream",
      "red": true,
      "restore_sha256": "84dcabf9f600dc63a4fe4a0fd3e6b9affca03f9e796c84a14835f7038d310b8d",
      "green_after_restore": true
    },
    {
      "id": "P_B2_4",
      "file": "src/adapter/bevy/build.rs",
      "edit": "the resolved feature reader pointed back at packages[].features (the declared table)",
      "named_test": "adapter::bevy::build::tests::the_metadata_feature_reader_reads_the_resolved_set_not_the_declared_table",
      "red": true,
      "restore_sha256": "7381b734a67f1a8107e1861f8ba9c2d625c24cd1dc9f4e40353d51cfcd0dc1e7",
      "green_after_restore": true
    },
    {
      "id": "P_B2_7",
      "file": "src/adapter/bevy/battery.rs",
      "edit": "the coin phase drops a failed read from the series again (the B2 behaviour)",
      "named_test": "adapter::bevy::battery::tests::a_vanished_surface_is_not_a_measured_failure",
      "red": true,
      "restore_sha256": "736c6ea03001b10dc0866ce9c08e6a2a4941b27a388d005512230e3ae03a0b39",
      "green_after_restore": true
    },
    {
      "id": "P_B2_9",
      "file": "src/adapter/bevy/brp.rs",
      "edit": "the id check accepts a reply with no id member again",
      "named_test": "adapter::bevy::brp::tests::a_reply_with_no_id_member_is_refused_when_an_id_is_expected",
      "red": true,
      "restore_sha256": "84dcabf9f600dc63a4fe4a0fd3e6b9affca03f9e796c84a14835f7038d310b8d",
      "green_after_restore": true
    }
  ],
  "forbidden_zone": {
    "tracked_rs_files": 111,
    "decisions_md_touched": false,
    "spikes_touched": false,
    "requirements_touched": false,
    "design_overview_touched": false,
    "design_detail_touched": false,
    "engine_tree_touched": false,
    "godot_mcp_touched": false,
    "cargo_toml_or_lock_touched": false,
    "runs_files_touched": 0,
    "dependencies_added": 0,
    "pushed": false
  },
  "residual_risks": {
    "measured": [
      "a contract check without register_type declarations reports the specific missing path and does not name the present ones",
      "removing the in-process fake's blocking restore reddens the suite (the in-process fake is now the pin, not a test-local server)",
      "the declared feature table is refused when the resolved graph lacks the frozen feature",
      "a build that outlives BuildRequest.timeout is killed and reported as AdapterError::BuildBudgetExceeded",
      "the readiness probe uses the configured endpoint and names it when it gives up",
      "a vanished coin/win surface is 'not observed', not a measured failure, and a false-answering surface stays measured"
    ],
    "inferred": [
      "whether the blocking restore is necessary on Windows beyond being present: removing it changed nothing observable, so it is pinned as a safeguard, not proven load-bearing",
      "whether a real hof_game spells every register_type in the form the source reader recognises (the reader is a source scanner, not a runtime registry read)",
      "the real cargo build + real cargo metadata path end to end: the readers were driven through their document seam and a source tree, not against a real game",
      "the real-machine smoke was not run (no engine)"
    ]
  },
  "declared_not_done": [
    "the forced rebuild (fingerprints cleared, every tracked .rs touched, gate rerun)",
    "a full gate run on the exact final bytes after the layout-only cargo fmt pass",
    "the ignored real-machine smokes",
    "the real cargo build end to end"
  ]
}
```

### How to read the verdict

`pass-with-declared-gaps` is not a claim that everything in the gate section was measured.  The twelve
inherited defects are all addressed in code with a test that reddens when the repair is removed; the
gap is that the final gate numbers were taken **before** a layout-only `cargo fmt` pass, and the
forced rebuild was not run because the dispatcher stopped further builds.  Both are named in
`declared_not_done` and repeated in §7 and §10.

## 0. The two direct answers

**B2-1 — can a real round now reach the build and then the contract check?**  **Yes, for a workspace
whose source declares the seven contract registrations.**  `prepare()` now has two readers with two
concerns, two pins and two reasons:

1. the **feature** reader reads the **resolved** graph (`resolve.nodes[].features` of the `bevy`
   package), hashes the frozen part and compares against `FEATURE_SET_SHA256`, with a reason about
   features;
2. the **contract** reader reads the game's own source for `register_type::<…>` declarations, maps
   the type names to the seven frozen paths, and `check_declared_contract_paths` compares against
   `adapter/bevy/contract.rs` with a reason that names the specific missing path and says what it
   compared.

The default policy no longer compares against an empty string: `BuildPolicy::lock_sha256` is an
`Option`, `default()` is explicitly unpinned, `BevyAdapter::at(workspace)` pins the lockfile it can
read, and `prepare()` either compares against a real pin or records that no comparison was requested.
The test
`adapter::bevy::tests::a_real_project_reaches_the_build_and_the_contract_check_with_coherent_reasons`
drives a real temp project through the **real** feature reader (over a `cargo metadata` document
injected at its seam) and the **real** source contract reader, with a fake builder, and asserts that
the build ran, that the adapter is lockfile-pinned, that all seven paths were read, and that the
prepared detail contains neither `pinned to` nor `missing`.  The plant `P_B2_1` (which removes the
source scan) reddens it.

**A contract failure names the specific missing path, not all seven.**  The test
`a_missing_contract_registration_names_the_specific_path` leaves `Grounded` out of the project and
asserts the message contains `hof_game::contract::Grounded`, does **not** contain
`hof_game::contract::Player`, and does not mention `bevy_remote`; it also asserts the build was
reached first.  The empty-lockfile-pin failure is gone because there is no empty pin to compare
against.

**B2-2 — does removing the blocking-restore now redden the suite?**  **Yes.**  The in-process
`FakeBrp` now records every accepted stream it puts back to blocking, through
`FakeBrp::blocking_restores()`, and the lib test
`adapter::bevy::brp::tests::the_fake_restores_blocking_on_every_accepted_stream` asserts it is `>= 1`.
The plant `P_B2_2` deletes the `set_nonblocking(false)` restore (and the counter it feeds) and the
test fails with exit 101; the byte-exact restore turns it green again.  This is a pin on the repair's
**presence**, not a proof that the repair is load-bearing on Windows — see §10.

## 1. The two hashes, old and new

| surface | old (B1) | current (B2, unchanged by B3) | moved by B3 |
|---|---|---|---|
| `sha256(canonical_json(CONTRACT))` | `4af153e77af87ceddb162c4b782701ee0b6c066a651d4e4b5d1e71f329649c69` | `792001e7e629ccc25d6c486eeb54360d83ffb208befa4ca5e430c6f0e747f4f9` | no |
| `sha256(canonical_json(tools/list))` | `e177325fe8b2036c355d37b9373b85b524f4a7f0d999e087711366bca661ae97` | `bcf03c0b06295cfd27cc0359a7fa272ed435bdf61525d67b08981c62d30e43b1` | no |
| feature-set document | `d6a90ba39e67b9e05fd28d97cc570dc989a03e8ec7a15ba93d077d5fe95d1f96` | same | no |

**B3 does not re-pin either frozen surface.**  That is the honest reading of "the two new hashes":
the two hashes that B2 re-pinned are still the live pins, and this batch had no reason to move them —
it changed readers and failure reasons, not the contract table or the tool list.  The values were
confirmed by the crate's own tests in the measured gate run
(`the_contract_hash_is_the_pinned_literal`,
`the_repinned_contract_hash_covers_seven_surfaces`,
`the_repinned_tool_list_hash_is_the_published_value`,
`the_feature_pin_is_unchanged_and_still_hashes_the_frozen_document`), which passed.  I did **not**
re-implement canonical JSON + SHA-256 independently in this session, so these are measured by the
crate's own computation, not by a second implementation.

## 2. The gate

| run | command | literal exit code | passed / failed / ignored / listed | result lines | warnings | log |
|---|---|---|---|---|---|---|
| baseline (pre-B3 tree) | `cargo test --offline` | **0** | **814 / 0 / 9 / 823** | 64 | 1 | `F:/b3-scratch/out/baseline.log` |
| final revision | `cargo test --offline` | **0** | **832 / 0 / 9 / 841** | 64 | 0 | `F:/b3-scratch/out/dev-full.log` |
| format (measured revision) | `cargo fmt --all --check` | **1** | 4 layout hunks in `battery.rs` | — | — | `F:/b3-scratch/out/fmt.log` |
| format (after `cargo fmt --all`) | `cargo fmt --all --check` | **0** | no output | — | — | `F:/b3-scratch/out/fmt2.log` |
| forced rebuild | fingerprints cleared + every tracked `.rs` touched | **not run** | — | — | — | — |

- **Baseline reproduced, not trusted.**  The B2 acceptance quoted 814/0/9/823.  I restored the
  pre-B3 bytes from a sha256-verified backup, ran the suite in `F:/b3-scratch/target-base`, and got
  the same numbers with literal exit code 0 — and one dead-code warning, the B2-12 defect.
- **Delta:** +18 passed, +0 ignored, 0 removals, 1 rename
  (`d3_the_fake_server_never_answers_a_request_it_did_not_read` →
  `d3_the_raw_socket_sees_a_complete_request_and_a_failed_read_is_refused`, because that test no
  longer claims to pin the in-process fake), −1 dead-code warning.
- The 9 ignored are the 7 pre-existing `e0..e6` smokes plus the two real-machine smokes (B1 and B2);
  **no `#[ignore]` was added**, and none was run.
- The final run was taken with no other cargo/rustc/test process started by me; the section is
  reproduced from a single run of the full suite in its own build directory.
- The run is **before the layout-only fmt pass**.  Mechanically, the post-fmt tree differs from the
  measured tree only in whitespace and commas, plus exactly two closure braces that rustfmt added in
  `build.rs` (character-level diff of `build.rs`, `contract.rs`, `tests/bevy_adapter_b2.rs`).  No
  expression, literal, control-flow or test name changed.  Even so, a full rerun on the exact final
  bytes was **not** performed and is declared, not claimed.

## 3. The twelve defects, one by one

### B2-1 (high) — the real path cannot succeed — **fixed**

- **What it was:** `BuildPolicy::default()` carried `lock_sha256: String::new()`, and the real
  `CargoMetadataFeatures` reader returned Bevy's feature names in `ResolvedFeatures.type_paths`,
  which `prepare()` fed to `check_registered_type_paths`.
- **What changed:**
  - `BuildPolicy.lock_sha256` is `Option<String>`; `default()` is explicitly unpinned; `pinned_to`
    pins a readable lockfile; `pinned_if_available` is what `BevyAdapter::at` uses; `prepare()`
    compares only against a real pin, with a reason naming both hashes, and otherwise records that
    no comparison was requested.
  - `ResolvedFeatures` now carries `features` (not `type_paths`); the feature check has its own pin
    (`FEATURE_SET_SHA256`) and its own reason.
  - A new `ContractPathReader` seam with the real `SourceContractPaths` reads the game's
    `register_type::<…>` declarations, and `check_declared_contract_paths` compares them against the
    seven frozen paths with a reason that names the missing path and the source it read.
- **Tests that catch its return:**
  `adapter::bevy::tests::a_real_project_reaches_the_build_and_the_contract_check_with_coherent_reasons`,
  `adapter::bevy::tests::a_missing_contract_registration_names_the_specific_path`,
  `adapter::bevy::tests::the_feature_check_has_its_own_reason_and_pin`,
  `adapter::bevy::build::tests::a_policy_pins_the_lockfile_it_can_read_and_says_so_when_it_cannot`,
  `adapter::bevy::build::tests::the_source_contract_reader_reads_register_type_declarations`,
  `adapter::bevy::contract::tests::a_declared_contract_failure_says_what_it_compared_and_which_path_is_missing`.
  Plant **P_B2_1** reddens the first.

### B2-2 (medium) — the timing repair is not pinned — **fixed**

- **What it was:** deleting the `set_nonblocking(false)` block left the whole 335-test lib suite
  green.
- **What changed:** the in-process `FakeBrp` counts successful blocking restores and exposes
  `blocking_restores()`; the lib test asserts a restore happened.
- **Test that catches its return:**
  `adapter::bevy::brp::tests::the_fake_restores_blocking_on_every_accepted_stream`.  Plant **P_B2_2**
  reddens it (exit 101), restore returns it to green.
- **Declared limit:** this pins the repair's presence; it does not prove the repair is necessary
  (removing it changed nothing observable here).

### B2-3 (medium) — the report is missing — **fixed**

- **What it was:** `BATCH-B2-REPORT.md` did not exist.
- **What changed:** this file (B3's own report, with the machine-readable block) and
  `.spec/bevy/BATCH-B2-RECONSTRUCTION.md`, which reconstructs B2 from `git diff --stat HEAD`, the
  hashes it moved, and the acceptance's findings, and states plainly that it is a reconstruction and
  that B2's intent cannot be recovered.
- **Test that catches its return:** there is no test for a document; the readers of this track are
  the check.

### B2-4 (medium) — the declared feature table is read instead of the resolved set — **fixed**

- **What it was:** `bevy_features` read `packages[].features`.
- **What changed:** `resolved_bevy_features` reads `resolve.nodes[].features` for the `bevy` package
  id (sorted, deduplicated); a document without a `resolve` section is refused explicitly rather than
  falling back to the declared table.
- **Test that catches its return:**
  `adapter::bevy::build::tests::the_metadata_feature_reader_reads_the_resolved_set_not_the_declared_table`.
  Plant **P_B2_4** reddens it.

### B2-5 (low) — the build timeout is measured, never enforced — **fixed**

- **What it was:** `CargoBuilder` blocked in `wait_with_output()`; `BuildRequest.timeout` was unused.
- **What changed:** `wait_with_timeout(child, timeout)` polls with a deadline, drains both pipes on
  reader threads, and on expiry kills the child (and, on Windows, its descendants via `taskkill /T`)
  and returns `ChildEnd::TimedOut` without joining the pipe readers (a killed build can leave a
  descendant holding the pipe).  `CargoBuilder` maps that to the new typed
  `AdapterError::BuildBudgetExceeded { budget_millis, observed_millis }`, which the gate classifies as
  `build_budget_exceeded`; `prepare()` propagates it instead of re-wrapping it as a transport error.
- **Tests that catch its return:**
  `adapter::bevy::build::tests::a_build_that_outlives_its_budget_is_killed_and_reported`,
  `adapter::bevy::build::tests::the_cargo_builder_honours_the_requests_timeout`.
- **Note:** `cache_hit` still keys on `Compiling bevy` lines.  It is not a defect on the work list;
  it remains a residual risk (see §10).

### B2-6 (low) — the endpoint override and the readiness probe disagree — **fixed**

- **What it was:** `LaunchConfig::endpoint()` was hard-wired to 15702 while the adapter set
  `HOF_BRP_ENDPOINT_OVERRIDE` for another endpoint.
- **What changed:** `LaunchConfig.endpoint_override: Option<String>`, honoured by both `endpoint()`
  and `probe_client()`; `BevyAdapter::launch_config()` is the single place the override and the
  game's environment are set, and `start()` uses it.
- **Tests that catch its return:**
  `adapter::bevy::launch::tests::the_readiness_probe_follows_the_configured_endpoint`,
  `adapter::bevy::launch::tests::a_probe_against_a_moved_endpoint_names_that_endpoint_when_it_gives_up`,
  `adapter::bevy::tests::a_moved_endpoint_reaches_the_readiness_probe_not_only_the_environment`.

### B2-7 (low) — a failed read becomes a measured failure — **fixed**

- **What it was:** the coin/win phase dropped a failed read from the series, so a vanished surface
  was reported as "the counter never rose above 0", `was_measured() == true`.
- **What changed:** any failed coin/win read in the phase turns the observation into
  `not observed: the \`<tool>\` read failed (…)`; `Observation::was_measured` treats a failure whose
  reason starts with `not observed` as **not measured**, so a read that answers `false` stays a
  measured failure.
- **Tests that catch its return:**
  `adapter::bevy::battery::tests::a_vanished_surface_is_not_a_measured_failure` (plant **P_B2_7**
  reddens it with the exact old message) and
  `adapter::bevy::battery::tests::a_read_that_answers_false_is_still_a_measured_failure` (the
  direction guard).

### B2-8 (low) — the dead branch in the takeoff criterion — **fixed**

- **What it was:** an empty `if !grounded_at_takeoff && baseline_grounded == Some(true)` branch, after
  which the phase read always won.
- **What changed:** `grounded_evidence = grounded_at_takeoff || baseline_grounded == Some(true)`
  decides; the phase's own reading is still kept as evidence and reported when neither saw the
  ground.
- **Test that catches its return:**
  `adapter::bevy::battery::tests::the_pre_injection_baseline_decides_the_grounded_criterion` (both
  directions).

### B2-9 (low) — a reply with no id member is accepted — **fixed**

- **What it was:** the id correlation only ran when the reply had an `id`.
- **What changed:** when an id is expected, a reply with **no** `id` member is `Malformed` with a
  reason that says which request was waiting.
- **Test that catches its return:**
  `adapter::bevy::brp::tests::a_reply_with_no_id_member_is_refused_when_an_id_is_expected`.  Plant
  **P_B2_9** reddens it.  The raw doubles in `tests/bevy_adapter_b2.rs` now echo the request id.

### B2-10 (low) — the by-construction pin is tautological — **fixed**

- **What it was:** `assert_eq!(PLAYER_PATH, contract_path("player_marker"))` is true by definition,
  because that is how the constant is defined.
- **What changed:** the integration test restates the **seven** expected paths as independent
  literals (`"hof_game::contract::Player"`, …, `"bevy_transform::components::transform::Transform"`)
  and then checks those literals are the contract table's values.  A path move now fails the test and
  must be re-pinned deliberately.
- **Test that catches its return:**
  `tests/bevy_adapter_b2.rs::d4_the_semantic_paths_are_the_contracts_paths_by_construction`.

### B2-11 (low) — the D3 test does not test the in-process fake — **fixed**

- **What it was:** the test spoke to a `RawServer` defined inside the test file, whose reader turned a
  failed read into an empty body it then answered.
- **What changed:** the pin for the timing repair moved to the crate-local lib test over the real
  `FakeBrp` (§B2-2); `tests/bevy_adapter_b2.rs`'s raw server now returns `Result` from its reader,
  records read failures, answers an unread request with an explicit `-32700`, and the test asserts no
  read failed.  The test was renamed to say what it actually pins.
- **Tests that catch its return:**
  `adapter::bevy::brp::tests::the_fake_restores_blocking_on_every_accepted_stream` (the repair) and
  `tests/bevy_adapter_b2.rs::d3_the_raw_socket_sees_a_complete_request_and_a_failed_read_is_refused`
  (the wire shape).

### B2-12 (low) — unused helper and its warning — **fixed**

- **What it was:** `brp::fake::malformed_request_reply` was never called; the gate compiled with one
  dead-code warning.
- **What changed:** the helper was removed (the fake inlines its own error document).
- **Test that catches its return:** the gate itself — the final full-suite run has **zero** warning
  lines, where the baseline had exactly one.  The baseline's single warning was this function.

## 4. Plants

Five controlled plants, each green → red → byte-exact restore → green.  Backup and restore used
`F:/b3-scratch/py/snap.py` and `restore.py` (sha256 recorded, mtime set explicitly to a future
stamp, post-restore hash asserted against the manifest).  `F:/b3-scratch/py/verify_manifest.py`
re-asserts every restored file.

| plant | file | edit | named test | red | restore sha256 |
|---|---|---|---|---|---|
| P_B2_1 | `src/adapter/bevy/build.rs` | source contract scan forced to find nothing | `a_real_project_reaches_the_build_and_the_contract_check_with_coherent_reasons` | yes (exit 101, "6 missing: …") | `7381b734…dc1e7` |
| P_B2_2 | `src/adapter/bevy/brp.rs` | blocking restore + counter removed | `the_fake_restores_blocking_on_every_accepted_stream` | yes (exit 101, "must have been put back to blocking") | `84dcabf9…310b8d` |
| P_B2_4 | `src/adapter/bevy/build.rs` | resolved reader pointed at `packages[].features` | `the_metadata_feature_reader_reads_the_resolved_set_not_the_declared_table` | yes (exit 101, declared set returned) | `7381b734…dc1e7` |
| P_B2_7 | `src/adapter/bevy/battery.rs` | failed coin read dropped from the series | `a_vanished_surface_is_not_a_measured_failure` | yes (exit 101, the old false-green message) | `736c6ea0…0a0b39` |
| P_B2_9 | `src/adapter/bevy/brp.rs` | id check only when the reply has an id | `a_reply_with_no_id_member_is_refused_when_an_id_is_expected` | yes (exit 101, `Ok(Number(1))`) | `84dcabf9…310b8d` |

After the last plant the whole 9-file working set was re-asserted equal to the work manifest, and the
only later change is the layout-only `cargo fmt` pass described in §2.

## 5. Forbidden-zone self-check

- **Tracked `.rs` files: 111** (`git ls-files '*.rs' | wc -l`; `git ls-tree -r HEAD` agrees).  This is
  the number the B1 report mis-stated as 101 (the count at `d0a4805`).
- `git diff --stat` for `DECISIONS.md`, `.spec/bevy/REQUIREMENTS.md`,
  `.spec/bevy/DESIGN-OVERVIEW.md`, `.spec/bevy/DESIGN-DETAIL.md`, `.spec/bevy/SPIKE-1-REPORT.md`,
  `.spec/bevy/SPIKE-2-REPORT.md`, `godot-mcp/**`, `Cargo.toml`, `Cargo.lock` is **empty**: none of the
  forbidden files was touched.
- `.spec/bevy/PRD.md` is byte-identical to its B2 state (unchanged by B3); only the two new `.spec`
  documents were added.
- `runs/**`: **0** files with an mtime after 2028-01-01 (the stamp this session used for its own
  restores); nothing was written under `runs/**` at any point.  All scratch, logs, backups and build
  directories live under `F:/b3-scratch/`.
- **No dependency was added**: `Cargo.toml` and `Cargo.lock` are byte-identical to `HEAD`, and the
  new code uses only `std`, `serde_json`, `tempfile` (dev) and the crate's existing helpers.
- **Nothing was pushed**; nothing of this batch was committed.  No `rm -rf` and no `git checkout --`
  was used: removals went through `F:/b3-scratch/py/rmtree.py`, which refuses any path not strictly
  inside `F:/b3-scratch`, and restores went through `restore.py`, which asserts sha256.

## 6. Warnings

The final full-suite run produced **zero** `warning:` lines.  The baseline produced exactly one, the
B2-12 dead-code warning for `brp::fake::malformed_request_reply`.  Removing the helper removed the
warning.

## 7. What is measured and what is not

**Measured (this session):**

- Baseline `814 / 0 / 9 / 823`, literal exit 0, one warning, in `F:/b3-scratch/target-base`.
- Final `832 / 0 / 9 / 841`, literal exit 0, zero warnings, in `F:/b3-scratch/target-dev`.
- `cargo fmt --all --check` exit 1 on the measured revision, exit 0 after the layout-only pass.
- Every one of the five plants red and green again, with sha256-asserted restores.
- Zero writes under `runs/**`; 111 tracked `.rs` files; forbidden diffs empty.

**Not measured / declared:**

- The forced rebuild (clearing the crate's fingerprint directories with Python glob + remove-tree,
  touching each tracked `.rs` file individually from `git ls-files`, rerunning the gate).  The
  dispatcher stopped further builds.
- A full gate run on the exact post-fmt bytes.
- Any live-engine round, the two ignored real-machine smokes, and a real `cargo build` /
  `cargo metadata` end to end.

## 8. For the next batch

1. **Run the forced rebuild** and a gate on the frozen final bytes; that is the only piece of the
   gate this batch could not finish.
2. **Commit B3 by decision, not by reset**, and keep the acceptance chain auditable.
3. If the contract check must be authoritative rather than a source scan, move it to the running
   game: read `world.list_components` / `world.list_resources` through BRP after readiness and
   compare the **registered** paths.  That would remove the source-scanner's dependency on how the
   game spells `register_type`.
4. Consider the `cache_hit` heuristic: it is still `no Compiling bevy line`, which is a warm/cold
   discriminator, not a proof that nothing was recompiled.

## 9. Commands and artefacts

| artefact | path |
|---|---|
| baseline log / exit | `F:/b3-scratch/out/baseline.log`, `baseline.exit` |
| final log / exit | `F:/b3-scratch/out/dev-full.log`, `dev-full.exit` |
| format logs | `F:/b3-scratch/out/fmt.log`, `fmt2.log` |
| backups (pre-B3) | `F:/b3-scratch/backup/b3/` + `b3-manifest.json` |
| working set (post-B3, pre-fmt) | `F:/b3-scratch/work/b3/` + `b3-manifest.json` |
| scripts | `F:/b3-scratch/py/{snap,restore,verify_manifest,rmtree}.py` |
