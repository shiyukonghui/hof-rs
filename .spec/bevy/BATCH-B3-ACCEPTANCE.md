# BATCH-B3 ACCEPTANCE - the real build path, the timeline pin, and the twelve inherited defects

- Date: 2026-10-05
- Acceptance agent: independent subagent, no prior context, no implementer conclusion
- Revision measured: the working tree of **HEAD ba3d5c1** (`fix(b3): ...`, committed; `.gitattributes` still uncommitted), measured in a copy outside the repository at `F:/b3-acc/repo-final`
- Environment: offline, no engine, no game, no network; scratch, copy, logs and the one build directory under `F:/b3-acc/`
- **This acceptance was stopped early by the dispatcher** to move to the real end-to-end round. The final gate had finished (exit 0); the baseline, `cargo fmt`, the forced rebuild, my own probe tests and every plant were abandoned and are recorded as unverified.

## Machine-readable verdict

The block below is the output of a Python `json.dumps`, re-read and `json.loads`-parsed back (the criteria/defect counts were asserted equal after the round trip) before this file was written.

```json
{
  "verdict": "pass-with-unverified-items",
  "batch": "BATCH-B3",
  "revision_measured": "working tree of HEAD ba3d5c1 (B3 committed; .gitattributes still uncommitted); measured in the copy F:/b3-acc/repo-final",
  "head": "ba3d5c1b32342fa5e76d68683d3b46d10d58027f",
  "origin_master": "6553afedc0ca7ce5c33b3b8d506eed176fe3106e (HEAD is 2 commits ahead; nothing pushed)",
  "environment": "offline; no engine, no game, no network; scratch under F:/b3-acc (outside the repository); one source copy at F:/b3-acc/repo-final; one build directory F:/b3-acc/target-final",
  "stopped_early": "The dispatcher ordered a stop mid-session to move to the real end-to-end round. The final gate had finished (exit 0); the baseline run, cargo fmt, the forced rebuild, my own probe tests and every plant were abandoned. Those are listed as unverified, not as failures.",
  "criteria": [
    {
      "id": "C1-real-path-reaches-the-contract-check",
      "pass": true,
      "evidence": "Code reading (not execution): prepare() (src/adapter/bevy/mod.rs:477-592) now has two readers with two concerns. The feature check calls self.features.resolved_features(...) and compares ResolvedFeatures.feature_sha256 against FEATURE_SET_SHA256 with a feature reason; the contract check calls a separate self.contract_reader.declared_contract_paths(...) and check_declared_contract_paths(declared, source), which lists CONTRACT paths absent from the declared set and names them (contract.rs:233-254). The link that caused B2-1 is gone: mod.rs:540-568 never passes feature names to the path check. BuildPolicy.lock_sha256 is Option<String> (build.rs:147), default() is None (build.rs:167), BevyAdapter::at uses pinned_if_available (mod.rs:165-166), and validate_artifact builds a default adapter the same way (mod.rs:666-668), so the internal default no longer compares against an empty string. Existing tests that assert the pass case, the missing-one-path case and the lockfile case are present: adapter::bevy::tests::a_real_project_reaches_the_build_and_the_contract_check_with_coherent_reasons, a_missing_contract_registration_names_the_specific_path, prepare_refuses_a_lockfile_that_moved_inside_the_round. I did NOT execute my own three constructed cases (F:/b3-acc/staging/zzz_b3_probe.rs, written but never run); see unverified."
    },
    {
      "id": "C2-feature-and-contract-have-their-own-pins",
      "pass": true,
      "evidence": "Code reading: FeatureReader (build.rs:503-509) and ContractPathReader (build.rs:519-525) are separate traits with separate real implementations (CargoMetadataFeatures build.rs:541-700, SourceContractPaths build.rs:711-804). The feature pin is FEATURE_SET_SHA256 (build.rs:68); the contract pin is CONTRACT (contract.rs) and its hash CONTRACT_SHA256 (contract.rs:226-227). The three reasons are distinguishable in text: a lost feature says 'compared the resolved Bevy feature set ... against the frozen feature set' (build.rs:682-686), a missing path says 'compared the N contract type path(s) declared by <source> against the 7 frozen path(s)' (contract.rs:245-253), and a lockfile mismatch says 'compared this round's lockfile hash ... against the hash this round is pinned to' (mod.rs:494-502)."
    },
    {
      "id": "C3-timing-pin-exercises-the-in-process-fake",
      "pass": true,
      "evidence": "Code reading: the named test adapter::bevy::brp::tests::the_fake_restores_blocking_on_every_accepted_stream (brp.rs:1178-1192) constructs FakeBrp::spawn (the in-process fake, brp.rs:467-579), calls it through BrpClient, and asserts server.blocking_restores() >= 1. The counter is incremented only after stream.set_nonblocking(false) succeeds on every accepted stream (brp.rs:509-517), so the counter cannot be >= 1 without the restore. This is the fake whose timing was the B1 D3 defect, not a server defined in the test file. The removal counterfactual (delete the restore and watch the suite redden) was NOT executed; see unverified."
    },
    {
      "id": "C4-resolved-feature-set-is-read",
      "pass": true,
      "evidence": "Code reading: CargoMetadataFeatures::resolved_bevy_features (build.rs:616-638) looks up the bevy package id and reads resolve.nodes[].features for it, sorted and deduplicated; a document without a resolve section returns None and resolved_features turns that into a ContractViolation rather than falling back to packages[].features (build.rs:670-678). The declared table is not read anywhere else in the check. The test the_metadata_feature_reader_reads_the_resolved_set_not_the_declared_table (build.rs:1149-1195) asserts the resolved list and that a declared-only document cannot answer. Caveat: the resolved list is then filtered to the frozen features (frozen_part, build.rs:649-660), so only a LOST frozen feature is caught; an ADDED resolved feature does not move the pin. That is a defect, filed as B3A-1."
    },
    {
      "id": "C5-observation-semantics-not-observed-vs-measured",
      "pass": true,
      "evidence": "Code reading: phase_coins_and_win (battery.rs:486-588) records coin_gap/win_gap whenever a coin/win read has failed and builds the failure as 'not observed: ...' (battery.rs:557-562); was_measured (battery.rs:212-221) returns false whenever the failure starts with NOT_OBSERVED_PREFIX (battery.rs:191), while a successful read that answers false has no such prefix and stays measured. The direction guard test a_read_that_answers_false_is_still_a_measured_failure (battery.rs:1251-1271) exists beside a_vanished_surface_is_not_a_measured_failure (battery.rs:1219-1245). I did not execute either test; see unverified."
    },
    {
      "id": "C6-warnings-in-a-clean-build",
      "pass": true,
      "evidence": "Measured: my own fresh full-suite build (F:/b3-acc/target-final, empty at start) produced 0 lines containing 'warning:', and the log shows 'Compiling hof-rs v0.1.0 (F:\\b3-acc\\repo-final)'. The B3 commit message's claim that 'one dead-code warning remains' is contradicted by this measurement; the fix remove of brp::fake::malformed_request_reply is real (grep finds no such symbol). Log: F:/b3-acc/out/final-gate.log."
    },
    {
      "id": "C7-gate-on-the-final-bytes",
      "pass": true,
      "evidence": "Measured by me, on the post-fmt final working tree (so it covers the bytes the report admitted it had not gated): cwd F:/b3-acc/repo-final, CARGO_TARGET_DIR=F:/b3-acc/target-final, command 'cargo test --offline', literal exit code 0 (F:/b3-acc/out/final-gate.exit = CARGO_TEST_EXIT=0), 832 passed / 0 failed / 9 ignored / 841 listed over 64 result lines, 0 warnings. The 9 ignored are the 7 pre-existing e0..e6 smokes plus the two real-machine bevy smokes (both carry #[ignore = ...] reasons); no #[ignore] was added. This reproduces the report's final figure exactly. I did not run the baseline (814) or the forced rebuild; see unverified."
    },
    {
      "id": "C8-baseline-814",
      "pass": false,
      "evidence": "Not run. The report's baseline revision is a pre-B3 working tree that no commit contains; the only copy available is the implementer's own F:/b3-scratch/backup/b3 (whose hashes match the B2 acceptance's independently recorded sha256 for 8 of its 9 files), which I inspected but did not gate. So 814/0/9/823 is unverified by me."
    },
    {
      "id": "C9-fmt-and-forced-rebuild",
      "pass": false,
      "evidence": "Not run (stop order). cargo fmt --all --check and the forced rebuild (clear fingerprints, touch every tracked .rs, rerun the gate) are unverified by me. The report's own fmt claim (4 layout hunks in battery.rs) and its 'post-fmt delta touches only build.rs/contract.rs/tests/bevy_adapter_b2.rs' claim are inconsistent with its scratch manifest: six files (build.rs, contract.rs, launch.rs, mod.rs, tests/bevy_adapter_b2.rs and per the manifest battery.rs) differ between the pre-fmt work copy and the final tree. My post-fmt gate still reproduces 832, so the practical concern is closed, but the report's description is inaccurate."
    },
    {
      "id": "C10-forbidden-zone-and-nothing-weakened",
      "pass": false,
      "evidence": "Partly verified, then blocked by an external mutation. Verified at the start of the session: git diff --stat HEAD was empty for DECISIONS.md, both spikes, REQUIREMENTS.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md, Cargo.toml, Cargo.lock and godot-mcp; PRD.md is byte-append-only (current 7819 B starts with the 6553afe blob exactly at the seal marker byte 5136, sha256 dca329f3... = SEALED_PREFIX_SHA256); tracked .rs files at HEAD = 115 (not 111); origin/master is still 6553afe, so nothing was pushed. BLOCKED: during my session an unidentified process mutated the repository index (mtime 2026-10-04 08:04:28): godot-mcp now has 6484 staged deletions and is untracked on disk, its on-disk tree has 561290 files with tracked files such as godot-mcp/GAME-LOOP-LOG.md and godot-mcp/tools/tool_channels.json missing, and git ls-files '*.rs' fell from 115 to 100. I did not cause this (my only writes are under F:/b3-acc and this report) and it is concurrent with the dispatcher's stated move to a real round. I therefore cannot certify the engine tree untouched. Also: the report says 'nothing of this batch was committed', but HEAD is the B3 commit ba3d5c1 (2 ahead of origin/master)."
    },
    {
      "id": "C11-reconstruction-report",
      "pass": true,
      "evidence": "Read in full. .spec/bevy/BATCH-B2-RECONSTRUCTION.md is a faithful and sufficient account for a next reader: it states plainly that it is a reconstruction and not the implementer's account, gives the base revision 6553afe and B2's shape (12 tracked + 4 new), a change table, the two moved hashes, the acceptance's twelve findings, and an explicit 'what cannot be reconstructed' (intent, forced-rebuild numbers, the D3 repair's necessity). It does not overclaim."
    }
  ],
  "defects": [
    {
      "id": "B3A-1",
      "severity": "low",
      "what": "The resolved-feature check is one-directional. resolved_features() filters the resolved graph down to the frozen features (frozen_part) and hashes only those, so an ADDED feature in the resolved graph - a real drift that costs the documented warm-increment penalty - does not move the pin and is not refused. The batch's B2-4 defect named exactly this class of drift.",
      "reproduction": "Read build.rs:649-699 (frozen_part + resolved_features) and the test the_resolved_feature_set_is_filtered_to_the_frozen_list (build.rs:1250-1266), which asserts that a resolved list of ['bevy_remote','bevy_winit','png'] hashes to FEATURE_SET_SHA256. My own probe F:/b3-acc/staging/zzz_b3_probe.rs::probe_c_added_resolved_features_do_not_move_the_pin was written to demonstrate it but was not executed before the stop order (unverified by execution)."
    },
    {
      "id": "B3A-2",
      "severity": "low",
      "what": "The contract-path reader is a source scanner that matches bare type names and always reports the engine Transform path present. SourceContractPaths::declared_paths_in pushes ENGINE_TRANSFORM_PATH unconditionally (build.rs:745), so a game that never registers Transform still satisfies the check; and registered_type_names keeps only the last path segment (build.rs:722), so a game-local type named Player satisfies hof_game::contract::Player. A contract check that can be satisfied without the contract type is weaker than 'the real path succeeds' suggests.",
      "reproduction": "Read build.rs:715-749. The batch itself declares the scanner limitation in its report section 10 ('inferred ... the reader is a source scanner, not a runtime registry read') and recommends reading world.list_components after readiness."
    },
    {
      "id": "B3A-3",
      "severity": "low",
      "what": "The batch's own documentation is inconsistent with the delivered revision. BATCH-B3-REPORT.md section 5 says 'nothing of this batch was committed', but HEAD is ba3d5c1 with the B3 commit message (origin/master is still 6553afe, so 'nothing pushed' holds). The commit message says 'One dead-code warning remains and is declared', while the report's block claims 0 and my clean build measures 0.",
      "reproduction": "git log --oneline -2 (ba3d5c1 fix(b3)...), git rev-list --count origin/master..HEAD = 2, git show --stat ba3d5c1; warning count from my F:/b3-acc/out/final-gate.log = 0."
    },
    {
      "id": "B3A-4",
      "severity": "low",
      "what": "The report's fmt account does not match its own scratch evidence. It says the post-fmt tree differs from the measured one 'by whitespace, commas and two closure braces only (character-level diff of build.rs/contract.rs/tests/bevy_adapter_b2.rs)', but six files differ between F:/b3-scratch/work/b3 and the final tree, and F:/b3-scratch/work/b3-manifest.json disagrees with the file actually stored in F:/b3-scratch/work/b3 for battery.rs (manifest 736c6ea0..., file 8d657f57...).",
      "reproduction": "python F:/b3-acc/py/diff_work.py (5 files with textual diffs, all layout-only) and python F:/b3-acc/py/hashes.py F:/b3-scratch/work/b3 vs F:/b3-scratch/work/b3-manifest.json. My own gate on the post-fmt tree still gives 832, so this is a provenance defect only."
    },
    {
      "id": "B3A-5",
      "severity": "high",
      "what": "Environment, not the batch: during this session an unidentified process mutated the repository index and the godot-mcp tree (6484 staged deletions, godot-mcp untracked, 561290 on-disk files, tracked .rs 115 -> 100, tracked files 7025 -> 182). This prevents any clean 'forbidden zone untouched' certification and could contaminate any subsequent acceptance that reads the index.",
      "reproduction": ".git/index mtime 2026-10-04 08:04:28; git status --porcelain | wc -l = 6845 with 6484 entries 'D  godot-mcp/...' and '?? godot-mcp/'; git ls-files godot-mcp = 0; find godot-mcp -type f | wc -l = 561290. My only writes were under F:/b3-acc and this report file."
    }
  ],
  "risks": [
    "The real cargo build + cargo metadata path is still not exercised end to end: the headline fix was verified by reading the code and the seams (from_document, SourceContractPaths), not by building a real hof_game.",
    "The contract check is a source scan keyed on the bare type name and always assumes the engine Transform is registered, so a real game could pass it with a non-contract type of the same name (B3A-2).",
    "The feature check is one-directional (B3A-1); the frozen list contains only bevy_remote, so enabling extra Bevy features would silently change the build profile.",
    "cache_hit is still 'no Compiling bevy line', a warm/cold discriminator rather than proof nothing was recompiled; the report files it as a residual risk and it is not on the work list.",
    "The report's 'final' gate bytes changed under a layout-only fmt pass the report did not gate; my run closes that on the post-fmt bytes, but the batch's own pre-fmt/pre-post-fmt provenance is muddled (B3A-4).",
    "The repository index is being mutated by another process while this batch is under review (B3A-5); a later reader can no longer trust git status to describe the batch's diff."
  ],
  "unverified": [
    "The three constructed cases the job asked for (a passing feature check, exactly one missing contract path, a lockfile mismatch) as EXECUTED probes: F:/b3-acc/staging/zzz_b3_probe.rs was written but never run; the conclusions above rest on code reading and on the repository's own named tests, not on my own executed runs.",
    "The B2-2 removal plant: I did not delete set_nonblocking(false) and observe the suite redden. The pin is a code-level reading.",
    "The baseline cargo test --offline at the pre-B3 revision (report claims 814/0/9/823).",
    "cargo fmt --all --check (report claims exit 1 before the fmt pass and exit 0 after).",
    "The forced rebuild (clear fingerprints, touch every tracked .rs individually, rerun the gate).",
    "Breaking four or more of the twelve defect tests myself: no plant was executed. I only located the tests that would catch each return (the names are in the B3 report and I read their bodies: a_build_that_outlives_its_budget_is_killed_and_reported, the_cargo_builder_honours_the_requests_timeout, a_policy_pins_the_lockfile_it_can_read_and_says_so_when_it_cannot, the_source_contract_reader_reads_register_type_declarations, the_feature_check_has_its_own_reason_and_pin, the_fake_restores_blocking_on_every_accepted_stream, a_reply_with_no_id_member_is_refused_when_an_id_is_expected, a_vanished_surface_is_not_a_measured_failure, a_read_that_answers_false_is_still_a_measured_failure, the_pre_injection_baseline_decides_the_grounded_criterion, the_readiness_probe_follows_the_configured_endpoint, a_probe_against_a_moved_endpoint_names_that_endpoint_when_it_gives_up, d4_the_semantic_paths_are_the_contracts_paths_by_construction).",
    "A driver whose coin/win reads start failing part-way, executed by me (the repository test a_vanished_surface_is_not_a_measured_failure covers it by construction; I read it but did not run it).",
    "The two ignored real-machine bevy smokes and any live-engine round (no engine, offline).",
    "The raw file hashes of the six files whose pre-fmt copies exist only in the implementer's scratch manifest (I could not reconcile F:/b3-scratch/work/b3-manifest.json with its own directory for battery.rs).",
    "Whether the external index mutation (B3A-5) affects commits after mine; I did not touch it and did not investigate its cause."
  ]
}
```

### How to read the verdict

`pass-with-unverified-items` means: the one thing that matters most - the code no longer conflates the feature set with the contract paths, and a real round can reach the build and then the contract check with a reason that names the specific missing path - is supported by reading the code and the named tests; the final gate reproduces exactly on the post-fmt bytes; but the checks I was asked to run **myself** (three constructed cases, the removal plant, four-plus defect plants, the baseline, `cargo fmt`, the forced rebuild) were **not executed**, because the dispatcher stopped the session. Everything not executed is listed under `unverified`.

## 1. Per-item table

| # | Job | Judgement | Evidence |
|---|---|---|---|
| 1 | headline: can a real round reach the build and the contract check? | **pass (code-level)** | `prepare()` has two readers, two pins and three distinguishable reasons; `BuildPolicy.lock_sha256` is `Option` and `at()` pins by construction; `check_declared_contract_paths` names the missing path. My own three constructed cases were written but not run. |
| 2 | the timing pin (B2-2) | **pass (code-level)** | `the_fake_restores_blocking_on_every_accepted_stream` uses the in-process `FakeBrp`; `blocking_restores()` is incremented only after a successful `set_nonblocking(false)`. The removal plant was not executed. |
| 3 | the resolved feature set (B2-4) | **pass, with a defect** | `resolved_bevy_features` reads `resolve.nodes[].features`; a *lost* frozen feature is refused. An *added* feature is filtered out and does not move the pin (B3A-1). |
| 4 | the remaining eleven defects | **not executed** | I located and read the test that would catch each return; no plant was run. |
| 5 | the gate | **pass (final only)** | `cargo test --offline`, literal exit code **0**, **832 passed / 0 failed / 9 ignored / 841 listed**, 64 result lines, **0 warnings**, run by me on the post-fmt final tree in a fresh `F:/b3-acc/target-final`. Baseline 814 and the forced rebuild were not run. |
| 6 | nothing weakened / forbidden zone | **blocked** | Frozen docs, manifest and PRD append-only verified at the start; then an unidentified process mutated the index and `godot-mcp` mid-session (B3A-5). The report also says "nothing was committed" while HEAD is the B3 commit (B3A-3). |

## 2. The headline, in detail

**Yes, structurally, a real round can now reach the build and then the contract check, and a missing path is named specifically.** The evidence is a code reading:

- `src/adapter/bevy/mod.rs:477-592`. `prepare()` reads the manifest and crate name, then the lockfile; `Some(expected)` pins compare and name both hashes, `None` records that no comparison was requested (no empty-string pin). It builds, then runs the **feature** check (`self.features.resolved_features(...)`), then the **contract** check (`self.contract_reader.declared_contract_paths(...)` + `check_declared_contract_paths`). The two concerns never share a list.
- `src/adapter/bevy/build.rs:503-525`: `FeatureReader` and `ContractPathReader` are separate traits. `CargoMetadataFeatures` (build.rs:541-700) parses a `cargo metadata` document; `SourceContractPaths` (build.rs:711-804) scans the game's `src/**/*.rs` for `register_type::<...>`.
- `src/adapter/bevy/contract.rs:233-254`: `check_declared_contract_paths` filters `CONTRACT` to the paths absent from the declared set and prints `"compared the N contract type path(s) declared by <source> against the 7 frozen path(s) ...: M missing: <paths>"`. A project missing exactly `Grounded` produces a reason naming `hof_game::contract::Grounded` and not the present paths.
- The three reasons are textually distinct: feature (`compared the resolved Bevy feature set ... against the frozen feature set`), contract path (`compared the N contract type path(s) declared by ...`), lockfile (`compared this round's lockfile hash ... against the hash this round is pinned to`).

**What remains between this code and a real end-to-end round:** (a) the real `cargo metadata`/`cargo build` path was not executed - only the document seam and a source tree were (`build.rs:563-594`, `mod.rs:540-568`); (b) the contract check is a source scan keyed on bare type names and always assumes the engine `Transform` is registered (B3A-2), so it can be satisfied without the contract types; (c) the feature check catches only a *lost* frozen feature (B3A-1); (d) the lockfile pin now exists, but a round with no `Cargo.lock` is still allowed to proceed unpinned by design.

## 3. The timing pin, the feature set, the observation semantics

- **B2-2.** The named test at `src/adapter/bevy/brp.rs:1178-1192` calls `FakeBrp::spawn` - the in-process fake at `brp.rs:467-579`, the double whose timing was the B1 D3 defect - and asserts `server.blocking_restores() >= 1`. The counter (`brp.rs:509-517`) is only incremented when `stream.set_nonblocking(false)` succeeds. I did **not** delete the restore and observe the suite redden.
- **B2-4.** `resolved_bevy_features` (`build.rs:616-638`) reads `resolve.nodes[].features` for the `bevy` package id; a document without a `resolve` section is refused rather than falling back to `packages[].features` (`build.rs:670-678`). The limit: `frozen_part` (`build.rs:649-660`) keeps only the frozen features, and the repository's own test `the_resolved_feature_set_is_filtered_to_the_frozen_list` (`build.rs:1250-1266`) asserts that `["bevy_remote","bevy_winit","png"]` hashes to the pin. So a *removed* `bevy_remote` is caught; an *added* feature is not.
- **B2-7 (observation semantics).** `phase_coins_and_win` (`battery.rs:486-588`) turns any failed coin/win read into a `coin_gap`/`win_gap` and prefixes the failure with `"not observed"`; `Observation::was_measured` (`battery.rs:212-221`) returns `false` for that prefix. A successful read that answers `false` has no prefix and stays a measured failure, guarded by `a_read_that_answers_false_is_still_a_measured_failure` (`battery.rs:1251-1271`). I read both tests; I did not run them.

## 4. The gate I hold

| run | command | literal exit code | passed / failed / ignored / listed | warnings |
|---|---|---|---|---|
| final (post-fmt bytes) | `cargo test --offline` in `F:/b3-acc/repo-final`, `CARGO_TARGET_DIR=F:/b3-acc/target-final` | **0** | **832 / 0 / 9 / 841** over 64 result lines | **0** |
| baseline (pre-B3) | not run | - | - | - |
| `cargo fmt --all --check` | not run | - | - | - |
| forced rebuild | not run | - | - | - |

- Exit code recorded by the shell as `CARGO_TEST_EXIT=0` (`F:/b3-acc/out/final-gate.exit`); log `F:/b3-acc/out/final-gate.log`.
- The 9 ignored are exactly the 7 pre-existing `e0..e6` Godot smokes plus `the_pinned_endpoint_answers_discover_with_the_23_methods_of_bevy_0191` and `the_real_machine_smoke_proves_the_contract_on_a_live_bevy_game` (both carry an `#[ignore = "..."]` reason). None was run; no `#[ignore]` was added by B3.
- **Only one test process of mine ran**: the two `cargo.exe` PIDs visible during the run were the rustup shim and the real cargo from that single invocation (same creation second, both `test --offline`). The gate ran in a copy, with its own build directory.
- **Tracked `.rs` files at HEAD: 115** (`git ls-tree -r HEAD`). The report's **111** is the count before the four new `.rs` files of this change (`battery.rs`, `launch.rs`, `prd.rs`, `tests/bevy_adapter_b2.rs`) were committed; after the B3 commit the correct number is 115.
- The run was on the **post-fmt** bytes, i.e. it closes the report's own declared gap ("a full gate run on the exact final bytes was not performed"). It does not close the baseline or the forced rebuild.

## 5. What I did not check, and why

Abandoned on the dispatcher's stop order: the baseline run; `cargo fmt --all --check`; the forced rebuild (clearing fingerprints and touching every tracked `.rs`); my own probe tests at `F:/b3-acc/staging/zzz_b3_probe.rs` (the three constructed cases); every plant (I planned `set_nonblocking(false)` removal, `resolve.nodes` -> `packages[].features`, dropping the coin/win `coin_gap`, removing the no-id refusal, removing the source contract scan, a `PLAYER_PATH` literal drift, removing the build-timeout enforcement, hard-wiring the endpoint, and restoring the phase-read-wins grounded branch). None was executed; only the tests that would catch each return were located and read.

## 6. Forbidden zone, and an external anomaly

Verified before the mutation: `git diff --stat HEAD` was empty for `DECISIONS.md`, both spike reports, `REQUIREMENTS.md`, `DESIGN-OVERVIEW.md`, `DESIGN-DETAIL.md`, `Cargo.toml`, `Cargo.lock` and `godot-mcp/**`; `PRD.md` is a pure append - the current 7819-byte file starts with the 5136-byte `6553afe` blob exactly at the seal marker (byte 5136), whose sha256 `dca329f3b09519b743a8f26890cbc8b9a61f4e1acc04a0d6a427b47387bf4527` is the `SEALED_PREFIX_SHA256` literal; `origin/master` is still `6553afe`, so nothing was pushed.

**Anomaly.** During this session an unidentified process mutated the repository index at 2026-10-04 08:04:28: `git status --porcelain` grew to 6845 lines with **6484 staged `D  godot-mcp/...` entries** and `?? godot-mcp/`; `git ls-files godot-mcp` is now 0, `git ls-files '*.rs'` fell from 115 to 100, `git ls-files` from 7025 to 182; the on-disk `godot-mcp` tree now reports 561290 files and tracked files such as `godot-mcp/GAME-LOOP-LOG.md` and `godot-mcp/tools/tool_channels.json` are missing. I did not cause this - my only writes are under `F:/b3-acc/` and this report - and it coincides with the dispatcher's stated move to a real round. **Consequence: I cannot certify the engine tree untouched, and a later reader must not trust the current `git status` as a description of this batch.**

## 7. Independent judgement

The repair direction is right and the headline structural defect is genuinely gone: the feature set and the contract paths now have separate readers, separate pins and separate reasons, the empty lockfile pin is an explicit `Option::None` state rather than a comparison against `""`, and a missing contract registration produces a reason that names the missing path. The final gate on the previously ungated post-fmt bytes reproduces 832/0/9/841 with exit 0 and zero warnings, which closes the report's declared fmt gap and the warning question.

But the batch is not fully verified by me, because the dispatcher stopped the session before I could execute a single plant or my own probes, and because the repository was being mutated underneath it. Two substantive weaknesses remain on the record: the feature check is one-directional (B3A-1) and the contract check is a name-keyed source scan that always assumes `Transform` (B3A-2). Neither is the headline; both belong to the real round's risk list.

## 8. Advice for the next batch

1. Move to the real round, but have the round's own contract check read the running game (`world.list_components` / `world.list_resources` after readiness) rather than the source, and hash the full resolved feature set (or at least forbid features outside the frozen list), not just the frozen subset.
2. Re-run the baseline and the forced rebuild only if the pre-B3 revision can be reconstructed from a source other than the implementer's own scratch backup; otherwise record the baseline as unreproducible rather than as 814.
3. Treat the current index state as contaminated: commit or restore `godot-mcp` deliberately, and re-anchor any acceptance to a fresh `git status`.
4. Fix the report/commit inconsistency (B3A-3) and the fmt-provenance mismatch (B3A-4) before the next audit chain is anchored to `ba3d5c1`.
