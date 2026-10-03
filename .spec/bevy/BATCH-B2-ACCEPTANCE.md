# BATCH-B2 ACCEPTANCE - the seventh reflectable surface, the sealed PRD prefix, output schemas in the tool list, and the inherited defects

- Date: 2026-10-04
- Acceptance agent: independent subagent, no prior context, no implementer conclusion
- Revision measured: the uncommitted B2 working tree on **6553afe** (12 tracked files modified, 4 new files)
- Environment: offline, no engine, no game, no network; scratch, logs, backups and copies under `F:/b2-acc/` (outside the repository)
- Deliverable: this file
- **The implementer's report does not exist** (`BATCH-B2-REPORT.md`): everything below was reconstructed from the working tree, the diff against the last accepted revision, and the specification.

## Machine-readable verdict

The block below is the output of a JSON serialiser (`F:/b2-acc/py/verdict.py`), re-read and `json.loads`-parsed back — the counts of criteria and defects were asserted equal after the round trip — before this file was written.

```json
{
  "verdict": "fail",
  "batch": "BATCH-B2",
  "revision_measured": "working tree on 6553afe, 12 tracked files modified + 4 new files, all uncommitted",
  "head": "6553afe (== origin/master; pushed by the dispatcher before this acceptance)",
  "environment": "offline, no engine, no game, no network; scratch under F:/b2-acc (outside the repository); one targeted copy at F:/b2-acc/scratch/repo",
  "why_fail": "The specification-level work is verified and strong: seven frozen surfaces with both hashes recomputed independently (and the B1 values reproduced exactly by removing the delta of this batch), the PRD change is a byte-exact append with a working prefix seal, the tool list really carries the eight output schemas inside its hash, and the default gate is green with a literal exit code of 0.  The batch fails on the deliverable it was asked to implement: the adapter's real build path cannot complete for a real project, the E2 artifact gate can never be green, one of the D3 repairs is not pinned by any test (removing it leaves the whole lib suite green), and the implementer report does not exist, so none of the above could be cross-checked against the implementer's own account.",
  "criteria": [
    {
      "id": "C1-contract-change",
      "pass": true,
      "evidence": "CONTRACT has seven entries; the seventh is surface frame_counter -> hof_game::contract::FrameCounter, reflect Resource, bound to bevy_wait_frames (test_repinned_contract_hash_covers_seven_surfaces, probe P12/P13).  My own canonical-JSON + SHA-256 reimplementation, run over the crate's own dumped documents, reproduces contract 792001e7e629ccc25d6c486eeb54360d83ffb208befa4ca5e430c6f0e747f4f9 and tool list bcf03c0b06295cfd27cc0359a7fa272ed435bdf61525d67b08981c62d30e43b1 word for word; both are stable when every object's keys are reversed and move when one character changes.  Removing the frame_counter entry from the dumped contract reproduces the B1 pin 4af153e77af87ceddb162c4b782701ee0b6c066a651d4e4b5d1e71f329649c69, and removing the outputSchema member from the eight semantic tools reproduces the B1 pin e177325fe8b2036c355d37b9373b85b524f4a7f0d999e087711366bca661ae97, so the delta of both hashes is exactly the change this batch claims.  Mutating one field inside one outputSchema moves the tool hash, i.e. the output shape is inside the hashed document.  All 23 generic tools have no outputSchema and all eight semantic tools do.  The frame a reading reports is the game's counter, not an ordinal: probe P2 drives a counter fixed at 777 and gets 777 on the first, second and third call; server.game_frame() has no ordinal counter at all and stays None when the counter cannot be read (P3, contract_violation)."
    },
    {
      "id": "C2-append-only-prd",
      "pass": true,
      "evidence": "The working PRD is exactly the HEAD blob followed by 2683 bytes: work.startswith(head_blob) is true, both are 0-CR LF, the prefix above the marker is byte-identical to the HEAD blob, is 5136 bytes and hashes to dca329f3b09519b743a8f26890cbc8b9a61f4e1acc04a0d6a427b47387bf4527, which is exactly the value and length the marker line and SEALED_PREFIX_SHA256/SEALED_PREFIX_BYTES state.  HEAD's blob carries no seal marker and no PRD.sha256 exists anywhere, so the appended text's statement that the document carried no prior seal is true and its first seal is a fresh measurement, not a continuation.  I copied the file outside the repository and rewrote one character above the seal (byte 66: the title's third character, the same length afterwards: 7819 bytes, prefix still 5136, prefix sha moved to a89a52e3ba7a8eeef9336dd73a606e88bf477845bd2b14c3c6d7118c4b4f7bb8); both the named integration test the_prd_sealed_prefix_is_byte_identical and the lib test prd::tests::the_real_documents_seal_is_the_frozen_literal went red with exit 101, and both were green again (exit 0) after a byte-identical restore whose sha256 I asserted.  The .gitattributes rule .spec/bevy/PRD.md -text is a necessary part of this: with the local core.autocrlf=true and no such rule a fresh checkout converts the file to CRLF (5217 bytes) and the length check fails, so the seal only survives because that rule was added."
    },
    {
      "id": "C3a-battery-five-observations",
      "pass": true,
      "evidence": "battery.rs wires all five phases through the real semantic layer: 1 movement (inject move +1 level, wait MOVE_FRAMES, compare x with an epsilon), 2 coins (baseline before any injection, then counts must start at 0 and never go backwards), 3 win (false then true, one-way), 4 jump (an arc of (game frame, y) samples with rising>0, falling>0 and peak>first), 5 a Grounded read before take-off.  Every observation keeps its raw CallEvidence, and each semantic call records the frame-counter read as its first BRP call.  My own trajectory counterexamples over JumpArc::classify: a monotone fall is RED (rise=0 fall=4, 'a monotone fall is not a jump'); a rise-then-fall passes; a stalled game yields one sample and no arc.  The counterexample that matters: a pure oscillation (-200,-199,-200,-199) passes (rise=2 fall=1) and a one-millimetre wobble (-200,-199.999,-200) passes, and a fall-then-rise-then-fall passes (rise=2 fall=3), so criterion 4 can be satisfied by a game that never jumps - the battery never checks that the injected jump caused the arc.  That matches the PRD's literal wording, so I file it as a risk rather than a defect."
    },
    {
      "id": "C3b-build-path",
      "pass": false,
      "evidence": "The build path does not work for a real project, on two independent counts.  (1) BuildPolicy::default() leaves lock_sha256 empty and nothing in production code calls pinned_to (only three test sites do), while prepare() refuses a lockfile whose hash is not the pin; probe P6 on a temporary workspace whose manifest is the frozen crate name returns launchable=false with reason 'the lockfile hash is 718475cd... but this round is pinned to :'.  validate_artifact constructs its own default-policy adapter internally, so the E2 artifact gate can never be green for any real workspace.  (2) The real feature reader returns Bevy's declared feature names in the ResolvedFeatures.type_paths field, and prepare() feeds that field to contract::check_registered_type_paths, which looks for the seven hof_game::contract::*/Transform paths; probe P17 composes the two public functions as prepare does and gets Err(ContractViolation) listing all seven contract paths as missing, after the build has already been paid for.  Also: the feature check reads Bevy's declared feature table (packages[].features) rather than the resolved/activated set, so it asserts little more than 'bevy_remote exists in Bevy 0.19.1'; BuildRequest.timeout is set from the cold budget but CargoBuilder never reads it and blocks in wait_with_output(), so the budget is measured and never enforced; cache_hit is decided only by the absence of a 'Compiling bevy' line, not by 'nothing was recompiled'; and the readiness probe can only ever use 15702 (LaunchConfig::endpoint() is hard-wired) while BevyAdapter::start sets HOF_BRP_ENDPOINT_OVERRIDE for an unpinned endpoint and its comment claims the probe follows the adapter's endpoint - it does not.  The build *policy* surface itself is right: shared target dir, frozen feature list, lockfile hash in meta.json, offline by default, a separate round-0 warm-up whose duration is kept out of the artifact's build time, and a budget overrun recorded rather than raised."
    },
    {
      "id": "C3c-readiness-and-launch",
      "pass": true,
      "evidence": "Readiness polls the main-world endpoint only: LaunchConfig::endpoint() returns brp::endpoint() = http://127.0.0.1:15702/ and probe_client() uses it (probe P10, launch tests); 15703 appears nowhere in the launch path.  start_game launches the same binary with HOF_GAME_HEADLESS=1 by default, drains stderr with one thread into a capped tail, detects a process that died before its endpoint answered and reports it separately from a timeout, stops the process on budget expiry, and stop asks via stdin then kills after a grace period while keeping the exit code and stderr tail.  The real-process tests (a stand-in that never binds, a missing binary, a shell that prints to stderr and exits 3) are OS facilities, not hardware, and they pass in the default gate.  The comment/behaviour mismatch about the unpinned-endpoint override is filed under C3b and as a defect; it cannot mislead a round, which is always pinned to 15702."
    },
    {
      "id": "C4-inherited-defects",
      "pass": false,
      "evidence": "D1 fixed and pinned; D2 fixed and pinned, with a residual; D3 partly fixed, its proven mechanism pinned but one repair not pinned at all; D4 fixed by construction with a tautological pin; D5 (the report's machine-readable block) cannot be met because the whole report is missing.  See the per-defect section and the plant table."
    },
    {
      "id": "C5-gate",
      "pass": true,
      "evidence": "cargo test --offline on the B2 working tree with a fresh CARGO_TARGET_DIR (F:/b2-acc/target-b2): literal exit code 0, 814 passed / 0 failed / 9 ignored over 64 result lines, 823 listed.  cargo fmt --all --check exit code 0 with no output.  No cargo, rustc or test process of mine was running before or after (tasklist).  Nothing was removed: 4 tests were renamed to match the changed semantics and 64 test functions were added, with zero net deletions (test_names.json; the 64 added functions explain 751->814 passed and 8->9 ignored).  The forced rebuild was still compiling when this report was written, so its numbers are reported as not completed."
    },
    {
      "id": "C6-forbidden-zone",
      "pass": true,
      "evidence": "git diff HEAD touches 12 tracked files (all inside src/, tests/, .spec/bevy/PRD.md and .gitattributes) plus 4 new files; DECISIONS.md, both spikes, REQUIREMENTS.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md, Cargo.toml, Cargo.lock, godot-mcp/** and .spec/hof-rs/** are byte-identical to HEAD (git diff --stat is empty for them).  No dependency was added.  runs/** has the same 7341 files with the same newest mtime (2026-10-03T05:47:27) as the B1 acceptance recorded, and zero files touched since 2026-10-04T00:00; .workspace/** is likewise untouched.  The four untracked JSON files (l.json, p2.json, pv.json, r.json) and the %DST% directory predate this batch (B1's report records the same four).  Nothing of this batch is committed or staged, and nothing of this batch was pushed; the tip 6553afe is the previous batch's own pushed commit, which the parent confirms is authorised by the accepted ledger entry."
    }
  ],
  "defects": [
    {
      "id": "B2-1",
      "severity": "high",
      "what": "The real prepare() path cannot succeed.  The default BuildPolicy carries no lockfile pin, and the real CargoMetadataFeatures reader returns Bevy feature names where prepare() then checks contract type paths, so a round either fails before the build with a nonsensical 'pinned to <empty>' reason or pays for the build and then fails with all seven contract paths reported missing.",
      "reproduction": "Probe P6: BevyAdapter::at(tempdir).validate_artifact(Project::at(tempdir)) with a Cargo.toml named hof_game -> launchable=false, reason 'the lockfile hash is 718475cd... but this round is pinned to :'.  Probe P17: CargoMetadataFeatures::bevy_features({packages:[bevy[...]]}) then contract::check_registered_type_paths(those names) -> Err(ContractViolation) naming hof_game::contract::Player ... InputIntent."
    },
    {
      "id": "B2-2",
      "severity": "medium",
      "what": "One of the D3 repairs is not pinned: the accepted stream is put back to blocking and reads retry on WouldBlock to a real deadline, but deleting the set_nonblocking(false) block leaves the entire lib suite green, so nothing would catch its removal.",
      "reproduction": "Plant P_D3c (remove the set_nonblocking(false) block): the named test stays green, exit 0.  Plant P_D3c_full (same plant, cargo test --offline --lib): 335 tests, exit 0, no failure.  The B2 integration test d3_the_fake_server_never_answers_a_request_it_did_not_read does not help here: it speaks to a RawServer defined inside that test file, not to the in-process FakeBrp the client's own tests use."
    },
    {
      "id": "B2-3",
      "severity": "medium",
      "what": "BATCH-B2-REPORT.md does not exist.  The batch landed its code uncommitted with no implementer account at all.",
      "reproduction": "ls .spec/bevy/ shows B1's report and acceptance but no B2 report; git status shows the B2 work as 12 modified plus 4 untracked files and no report among them."
    },
    {
      "id": "B2-4",
      "severity": "medium",
      "what": "The frozen feature set is not really verified: CargoMetadataFeatures::bevy_features reads the declared feature table of the bevy package (packages[].features), not the set the round resolved and compiled (resolve.nodes[].features), so a feature-set drift that costs the documented 236 s warm increment would pass the check.",
      "reproduction": "Read build.rs::bevy_features (package.get(\"features\")) and the test the_metadata_feature_reader_finds_the_bevy_package, which enshrines exactly that reading; probe P17 shows the resulting list is what prepare() hashes and then treats as type paths."
    },
    {
      "id": "B2-5",
      "severity": "low",
      "what": "BuildRequest.timeout is set from the cold budget but the real builder never reads it and blocks in wait_with_output(), so a hung cargo build hangs the round; the budget is only measured after the fact, and cache_hit is decided solely by the absence of a 'Compiling bevy' line.",
      "reproduction": "Probe P18: the production part of CargoBuilder contains no reference to `timeout` and does contain wait_with_output; build.rs::CargoBuilder::build and BuildOutcome.cache_hit."
    },
    {
      "id": "B2-6",
      "severity": "low",
      "what": "A semantic call that cannot read the frame counter is an error (good), but BevyAdapter::start sets HOF_BRP_ENDPOINT_OVERRIDE when the endpoint is not pinned and its comment says the readiness probe then points at the adapter's endpoint; the probe can only ever use 15702, so a test against a fake endpoint would wait 30 s on the wrong port.",
      "reproduction": "Probe P10: adapter.with_endpoint(19999).endpoint()=19999, while LaunchConfig::default().endpoint() is still http://127.0.0.1:15702/."
    },
    {
      "id": "B2-7",
      "severity": "low",
      "what": "The battery drops a failed read from the coin/win series instead of turning the observation into 'not observed', so a surface that disappears mid-phase is reported as a measured failure ('the coin counter never rose above 0', 'the win flag never became true (1 readings, all false)') with was_measured()=true.",
      "reproduction": "Probe P14 with a driver whose coin/win reads succeed twice and then return Reading::not_observed: coins failure='the coin counter never rose above 0 (last reading 0)', win failure='the win flag never became true (1 readings, all false)', both was_measured()=true."
    },
    {
      "id": "B2-8",
      "severity": "low",
      "what": "Criterion 5 has a dead branch: phase_jump's comment says the pre-injection baseline is the stronger evidence when the jump-phase read is false, but the code marks the observation false from the phase read regardless of the baseline.",
      "reproduction": "Probe P15 with a driver whose two baseline Grounded reads are true and whose jump-phase read is false: observed=false, failure='`Grounded` read false immediately before take-off (game frame 91)'.  Read battery.rs phase_jump lines 567-570 against lines 590-601."
    },
    {
      "id": "B2-9",
      "severity": "low",
      "what": "The D2 id check still accepts a reply that carries no id member at all: read_document_for only compares when the reply has an `id`, so {\"jsonrpc\":\"2.0\",\"result\":1} answers any pending request.",
      "reproduction": "Probe P5: read_document_for(no_id, Some(9)) is Ok; stale and string ids are correctly refused."
    },
    {
      "id": "B2-10",
      "severity": "low",
      "what": "The D4 pin is tautological for the current source shape: the test compares each semantic path constant with contract_path(same surface), and each constant is defined as exactly that call, so it can only catch a drift that someone reintroduces by hand; the 'by construction' guarantee itself rests on reading the const initialisers, not on the test.",
      "reproduction": "Plant P_D4 (PLAYER_PATH replaced by a wrong literal) reddens d4_the_semantic_paths_are_the_contracts_paths_by_construction, which proves the pin catches drift; the same assertion is true by definition for the shipped source."
    },
    {
      "id": "B2-11",
      "severity": "low",
      "what": "tests/bevy_adapter_b2.rs's D3 test exercises a RawServer written inside the test file, not the in-process FakeBrp whose timing dependence was the actual D3 defect, and its reader still turns a failed read into an empty body that it records and answers (only the test's later serde_json::from_str of that body turns an empty read into a failure).",
      "reproduction": "tests/bevy_adapter_b2.rs lines 62-73 (read, push and answer whatever read_http_body returned) and 112-134 (Err(_) => break, then String::new())."
    },
    {
      "id": "B2-12",
      "severity": "low",
      "what": "The batch adds a test-only helper brp::fake::malformed_request_reply that nothing calls; the gate compiles with one dead-code warning, and the D3 error document is inlined separately in the fake.",
      "reproduction": "cargo test output: 'warning: function `malformed_request_reply` is never used' at src/adapter/bevy/brp.rs:745."
    }
  ],
  "risks": [
    "Criterion 4 is necessary but not sufficient: a pure vertical oscillation, a one-millimetre wobble or a fall-then-rise-then-fall passes it, and the battery never checks that the injected jump intent caused the arc.  A next batch could add a control window (sample before the press) without changing the PRD.",
    "bevy_wait_frames still calls the wall-clock FrameWaiter first and then polls the counter, so a default-gate test of a frozen counter spends the 2 s floor; the reported frame is a real counter reading, but the wait is bounded by wall time when the counter is slow.",
    "The frame counter read and the surface read of one call share the same JSON-RPC id (exec_step is passed the evidence seq), so the id correlation cannot distinguish two replies to the same tool call; harmless with one connection per call, but it is the same class as D2.",
    "The whole B2 change is uncommitted and the implementer report is missing, so a reader has to reconstruct intent from code and the dispatcher's orientation, which is exactly what this acceptance had to do.",
    "The push of 6553afe replaced the B1 revision: B1's acceptance is anchored to f100e2f, which is no longer an ancestor of HEAD (its src/ and tests/ are byte-identical to 6553afe's, and the acceptance, the report revision and D297 ride in the new commit).  The parent confirms the push is authorised by the accepted ledger entry; the audit trail still needed a reset-plus-recommit to reconstruct.",
    "The seal only survives because .gitattributes pins PRD.md to -text; anyone who checks the file out with a different attribute set (or copies it through a CRLF-normalising tool) gets a red seal test for a reason that is not a spec violation.",
    "The ignored real-machine smoke was not run (no engine, offline), so the endpoint/version/frame-counter claims of the real contract remain unverified on hardware."
  ],
  "unverified": [
    "A baseline full-suite run at HEAD: I did not run one, so the +63 passed / +1 ignored delta is established from the test-name diff (4 renames, 0 deletions, 64 added functions) and from the counts, not from two measured runs.",
    "The forced rebuild (fingerprints cleared, all 111 tracked .rs files touched individually with content hashes asserted unchanged, then cargo test --offline) was still compiling when this report was written; its literal exit code and counts are not reported.",
    "The ignored real-machine smoke tests (tests/bevy_adapter_b1.rs and tests/bevy_adapter_b2.rs) and any live-engine round; offline by order, no engine and no game on this machine.",
    "The real CargoBuilder / cargo metadata path end to end: I established the two failures by composing the public functions and reading the code, not by running a real build against a real hof_game (there is no game).",
    "The D3 'accepted stream must block' repair is marked unverified-as-needed rather than fixed: removing it changes nothing observable in my runs, so I cannot say whether it is necessary under load.",
    "SPIKE-1 and SPIKE-2 measurements themselves (23 methods, 60.3 FPS, batch non-atomicity, the 2.04 s refused connect); I only checked that the code does not contradict them.",
    "+watch streaming paths and any end-to-end round through BevyMcpServer against a real BRP endpoint.",
    "The WouldBlock retry-to-deadline branch inside fake::read_request: no default-gate test drives a request that stalls mid-body without closing, so I did not observe that branch execute."
  ]
}
```

### How to read this verdict

- `verdict: fail` is about the **adapter body** the batch was asked to implement, not about the
  specification work.  Jobs 1, 2 and the battery wiring are verified and reproduced independently;
  the build path cannot complete for a real project (`B2-1`), one inherited-defect repair is not
  pinned (`B2-2`) and the implementer report is missing (`B2-3`).
- Every value below was produced by me: my own canonical-JSON + SHA-256 implementation, my own
  plants in a copy outside the repository, my own probes compiled into that copy, and one gate run
  in a fresh build directory.

## 1. Per-item table

| # | Job | Judgement | Evidence (all produced by me) |
|---|---|---|---|
| 1 | the contract change | **pass** | seven surfaces; both hashes recomputed independently and the B1 values reproduced by removing the delta; `outputSchema` on all 8 semantic verbs and no generic verb; the frame is the game's counter (777/777/777) |
| 2 | the append-only requirement | **pass** | `startswith(HEAD blob)`, 5136-byte prefix, 0 CR, sha `dca329f3…`, no prior seal, and a one-byte rewrite above the seal turns both seal tests red |
| 3a | the battery's five observations | **pass** | all five phases wired with raw calls kept; monotone fall red, rise-then-fall green, stalled game no arc; but a non-jump oscillation also passes (risk) |
| 3b | the build path | **fail** | default policy is unpinned, the real feature reader feeds feature names to the type-path check, the budget is not enforced, the feature check reads declared features |
| 3c | readiness and launch | **pass** | 15702 only, same-binary headless switch, stderr tail, dead-process vs timeout, stop preserves evidence; the unpinned-endpoint override is inconsistent but unreachable in a round |
| 4 | the inherited defects | **fail** | D1/D2/D4 fixed and pinned, D3's proven mechanism pinned but its blocking repair not pinned at all, the b2 D3 test does not test the in-process fake, D5 has no report to be in |
| 5 | the gate | **pass** | `cargo test --offline` **literal exit code 0**, **814 / 0 / 9** over 64 result lines (823 listed); `cargo fmt --all --check` exit 0; 4 renames, 0 deletions, +64 test fns; the forced rebuild did not finish before this report |
| 6 | nothing weakened, forbidden zone | **pass** | 16 B2 files only; DECISIONS.md, the spikes, the frozen design docs, `Cargo.toml`/`Cargo.lock`, `godot-mcp/**` and `runs/**` untouched; no dependency added; nothing staged, committed or pushed by this batch |

## 2. The two re-pinned hashes, as I recomputed them

| surface | B1 value (old) | B2 value (new) |
|---|---|---|
| contract `sha256(canonical_json(CONTRACT))` | `4af153e77af87ceddb162c4b782701ee0b6c066a651d4e4b5d1e71f329649c69` | `792001e7e629ccc25d6c486eeb54360d83ffb208befa4ca5e430c6f0e747f4f9` |
| tool list `sha256(canonical_json(tools/list))` | `e177325fe8b2036c355d37b9373b85b524f4a7f0d999e087711366bca661ae97` | `bcf03c0b06295cfd27cc0359a7fa272ed435bdf61525d67b08981c62d30e43b1` |
| feature set (unchanged) | `d6a90ba39e67b9e05fd28d97cc570dc989a03e8ec7a15ba93d077d5fe95d1f96` | same |

My own implementation (`F:/b2-acc/py/hashes.py`) canonicalises the documents the crate dumps
(`p1_dump_frozen_documents`) and agrees with the crate's own canonical bytes and with the pins.
Reversing every object's key order leaves both hashes unchanged; changing one character in either
document moves it.  The **old** values are not taken from the report: removing the `frame_counter`
entry from the dumped contract produces `4af153e7…` exactly, and removing `outputSchema` from the
eight semantic tools produces `e177325f…` exactly (`F:/b2-acc/py/hash_delta.py`), so the delta of
this batch is precisely "one contract entry + eight output schemas".  A one-field mutation inside
one `outputSchema` moves the tool hash, i.e. the return shape is inside the frozen document.

The seventh surface: `frame_counter -> hof_game::contract::FrameCounter`, `Resource`, bound to
`bevy_wait_frames`; the `frame` field's own description in `bevy_player_transform`'s output schema
says "the GAME's own frame (hof_game::contract::FrameCounter), never the adapter's observation
ordinal".  The server keeps no observation ordinal (`self.frame` is gone; `game_frame: Option<u64>`
starts `None`), and a counter fixed at 777 is reported as 777 on three successive calls (probe P2),
while an unreadable counter is a `contract_violation` and leaves `game_frame()` `None` (probe P3).

## 3. The append-only requirement

- The working PRD is `HEAD`'s blob followed by 2683 bytes: `work.startswith(orig)` is **true**,
  both are pure LF (**0 CR**), and the prefix above the marker line is byte-identical to the HEAD
  blob.
- Prefix length **5136 bytes**, sha256 `dca329f3b09519b743a8f26890cbc8b9a61f4e1acc04a0d6a427b47387bf4527`
  — exactly what the marker line and `SEALED_PREFIX_SHA256`/`SEALED_PREFIX_BYTES` state.
- **The document carried no prior seal, and the batch says so:** HEAD's blob contains no
  `<!-- hof-rs:sealed-prefix` marker and no `PRD.sha256` exists anywhere in the repository.  The
  appended text states this plainly ("本文件在本次追加之前从未被封印过"), so this is honestly
  presented as the *first* seal, not a continuation, and its value is a measurement of the file as
  it stood before the append.
- The seal test is `tests/bevy_adapter_b2.rs::the_prd_sealed_prefix_is_byte_identical`, with a
  second copy of the check in `prd::tests::the_real_documents_seal_is_the_frozen_literal`.
- **I made the seal red myself.**  On the copy (`F:/b2-acc/scratch/repo`) I rewrote one character
  above the marker (byte 66, the title), leaving the length at 7819 bytes and the prefix at 5136
  bytes; the prefix sha moved to `a89a52e3ba7a8eeef9336dd73a606e88bf477845bd2b14c3c6d7118c4b4f7bb8`
  and both named tests failed with exit 101.  After a byte-identical restore (sha256 asserted) both
  were green again (exit 0).
- `.gitattributes` gained `.spec/bevy/PRD.md -text`.  This is a necessary part of the seal rather
  than an unrelated edit: this repository has `core.autocrlf=true`, with no such rule a fresh
  checkout converts the file to CRLF (5217 bytes / 81 CR) and the *length* check inside `verify`
  fails, so the seal would only pass in a normalised working tree.  The change is in the same
  documented style as the existing DR-58/70/76 byte-frozen entries.

## 4. My own plants and counterexamples

Applied to a copy **outside the repository**, each with a backup, an explicit future timestamp, a
sha256 assert that the restored file equals the backup, and a green control afterwards
(`F:/b2-acc/py/plants.py`, records in `F:/b2-acc/out/plant-*.json`):

| plant | file | edit | named test | result |
|---|---|---|---|---|
| P_D1 | `brp.rs` | object check removed, missing `result` -> `Ok(null)` | `brp::tests::valid_json_that_is_not_a_json_rpc_document_is_malformed` **and** `d1_valid_json_that_is_not_json_rpc_is_malformed` | both **RED** (exit 101), control **green** |
| P_D2 | `brp.rs` | id correlation block removed | `brp::tests::a_reply_whose_id_is_not_the_requests_is_refused` **and** `d2_a_reply_for_another_request_is_refused` | both **RED** (101), control **green** |
| P_D3a | `brp.rs` | `content_length` scan aborts on the colon-less request line again | `brp::tests::the_fake_content_length_scan_skips_the_request_line` | **RED** (101), control **green** |
| P_D3b | `brp.rs` | short body -> `break` (empty Ok) instead of `Err` | `brp::tests::a_request_whose_body_never_arrives_is_a_failed_read` | **RED** (101), control **green** |
| P_D3c | `brp.rs` | `set_nonblocking(false)` on the accepted stream removed | `brp::tests::the_fake_accepts_a_well_formed_request_and_records_it_whole` | **GREEN** — not pinned |
| P_D3c_full | `brp.rs` | same, whole lib suite | all 335 lib tests | **GREEN** (exit 0) — not pinned |
| P_D4 | `semantic.rs` | `PLAYER_PATH` literal drift | `d4_the_semantic_paths_are_the_contracts_paths_by_construction` | **RED** (101), control **green** |
| P_SEAL | `.spec/bevy/PRD.md` | one character above the seal (byte 66) | `the_prd_sealed_prefix_is_byte_identical` **and** `prd::tests::the_real_documents_seal_is_the_frozen_literal` | both **RED** (101), control **green** |

**The D3 question, answered.**  The B2 integration test
`d3_the_fake_server_never_answers_a_request_it_did_not_read` speaks HTTP to a `RawServer` written
inside the test file (lines 62-73 answer whatever `read_http_body` returned, and lines 112-134 turn
a read error into `String::new()`), **not** to the in-process `FakeBrp` whose timing dependence the
B1 acceptance actually observed.  So that test does not protect the flaky path at all; it protects
its own double, and only because its later `serde_json::from_str` of the recorded body panics on an
empty one.

What does protect the flaky path is the pair of lib tests: the `content_length` scan (the mechanism
the B1 acceptance proved, `P_D3a` goes red when reverted) and "a failed read is an `Err`, not an
empty request" (`P_D3b` goes red when reverted).  The third repair — forcing the accepted stream
back to blocking and retrying `WouldBlock` to a deadline — is **not pinned**: deleting the
`set_nonblocking(false)` lines leaves the named test green and the whole 335-test lib suite green
(exit 0).  I therefore cannot state whether that repair is necessary; I can state that nothing
would notice its removal.

**The jump counterexamples** (probe P7): a monotone fall is **red** (`rise=0 fall=4`, "a monotone
fall is not a jump"); a rise then fall **passes** (`rise=2 fall=2 peak=-140 first=-200`); a
fall-then-rise-then-fall **passes** (`rise=2 fall=3`); a pure oscillation (`-200,-199,-200,-199`)
**passes**; a one-millimetre wobble (`-200,-199.999,-200`) **passes**; a stalled game produces one
sample and no arc.  So **yes, criterion ④ can be satisfied by a game that never jumps** — the
battery never checks that the injected jump caused the arc, only that some window of `y` samples
both rose and fell.  The PRD's wording is literally "rising and falling steps", so this is the
criterion as specified; I file it as a risk, not a defect.

## 5. The inherited defects, one by one

| defect | fixed in the code? | would the pin catch its return? | how I know |
|---|---|---|---|
| **D1** valid JSON that is not a JSON-RPC document must be `Malformed` | **yes** — `read_document_for` requires an object and a `result` (or non-null `error`) member | **yes** — both the lib test and the integration test redden when I restore the loose behaviour (`P_D1`) | plant P_D1, probes P5 |
| **D2** a reply whose id is not the request's must be refused | **yes**, with a residual | **yes** for a mismatching or non-numeric id (`P_D2`); a reply with **no** id member is still accepted (probe P5) | plant P_D2 |
| **D3a** the fake's `content_length` scan must skip the colon-less request line | **yes** | **yes** — red when reverted (`P_D3a`) | plant P_D3a |
| **D3b** a failed request read must fail, not become an empty request | **yes** (`read_request -> Result`, failure recorded in `read_failures()` and answered with an explicit `-32700`) | **yes** — red when the short body is `break`-ed again (`P_D3b`) | plant P_D3b |
| **D3c** the accepted stream must block and `WouldBlock` must be retried to a deadline | **in the code**, but | **no** — removing it leaves the named test and the whole lib suite green (`P_D3c`, `P_D3c_full`); the b2 test that claims to check the fake uses its own RawServer | plants P_D3c/P_D3c_full |
| **D4** the semantic paths must be bound to the contract by construction | **yes** — every constant is `contract::contract_path(surface)`, so a surface rename is a compile-time failure | **partly** — the pin reddens on a reintroduced literal (`P_D4`), but for the shipped source the assertion is true by definition, so the guarantee rests on the const initialisers | plant P_D4, probe P12 |
| **D5** the report must carry a machine-readable block | **no report exists at all** | n/a | `BATCH-B2-REPORT.md` is absent |

## 6. The gate

| run | command | literal exit code | passed / failed / ignored / listed | log |
|---|---|---|---|---|
| format | `cargo fmt --all --check` | **0** | no output | `F:/b2-acc/out/fmt.log` |
| clean full suite | `cargo test --offline` (`CARGO_TARGET_DIR=F:/b2-acc/target-b2`) | **0** | **814 / 0 / 9 / 823** over 64 result lines | `F:/b2-acc/out/gate-full.log` |
| forced rebuild | fingerprints cleared (65 `hof-rs-*` dirs), all 111 tracked `.rs` touched individually (content sha256 asserted unchanged) | not finished when this report was written | — | `F:/b2-acc/out/gate-rebuild.log` (in progress) |

- **Tracked `.rs` files: 111** (`git ls-files '*.rs' | wc -l`, and `git ls-tree -r HEAD` agrees) —
  the number a previous batch mis-stated as 101, which is the count at `d0a4805`.
- The 9 ignored are the 7 pre-existing `e0..e6` smokes plus the two deliberately ignored
  real-machine smokes (one from B1, one new in B2).  Both were never run.
- **No test was removed**: comparing test-function names at HEAD with the working tree finds 4
  renames (`the_contract_is_six_surfaces_…` -> `…seven…`, `frame_advance_and_health_need_no_brp_call`
  -> `frame_advance_waits_on_the_frame_counter_and_health_needs_no_call`,
  `a_semantic_read_issues_one_call_and_projects_the_named_fields` ->
  `a_semantic_read_asks_for_the_component_it_projects`,
  `frame_advance_moves_the_ordinal_and_reports_it` ->
  `frame_advance_waits_for_the_games_counter_and_reports_where_it_got_to`) and 64 added functions,
  with zero net deletions.  The +64 explains 751->814 passed and 8->9 ignored.
- **No second test process of mine was running** (`tasklist` for cargo/rustc/hof_rs before and after:
  none).  Plant runs and probe runs finished before the gate started; the clean gate is the only
  measurement reported.
- The build prints one dead-code warning (`malformed_request_reply` is never used, defect `B2-12`).

## 7. Nothing weakened and no forbidden zone

- `git diff --stat HEAD` covers exactly the 16 B2 files in the table below; `DECISIONS.md`, both
  spike reports, `REQUIREMENTS.md`, `DESIGN-OVERVIEW.md`, `DESIGN-DETAIL.md`, `Cargo.toml`,
  `Cargo.lock`, `godot-mcp/**` and `.spec/hof-rs/**` are untouched.
- No dependency was added (the manifest and lockfile are unchanged; the new code uses only
  pre-existing `serde`, `serde_json`, `thiserror`, `ureq`, `tempfile` and `std`).
- `runs/**`: the same **7341** files with the same newest mtime
  (`runs/smoke-t16/evidence/round/evidence_refresh.txt`, 2026-10-03T05:47:27) that the B1
  acceptance recorded, and **0** files touched since 2026-10-04T00:00.  `.workspace/**` (851 files)
  likewise 0 touched.  Nothing of mine was written under `runs/**` or any workspace.
- The four untracked JSON files (`l.json`, `p2.json`, `pv.json`, `r.json`) and the tracked `%DST%`
  fixture directory predate this batch; B1's report records the same four JSON files.
- **The push.**  `origin/master` is `6553afe` with reflog entry `update by push`, i.e. the previous
  batch's revision was pushed (together with the B1 acceptance, the report revision and D296/D297).
  The parent states this is authorised because the previous batch's acceptance passed and the gate
  ledger records that commit, so I report it as authorised rather than as a violation.  The audit
  point that remains: the tip was produced by `reset` to `8535257` plus a recommit, so B1's accepted
  `f100e2f` is no longer an ancestor of HEAD even though its `src/` and `tests/` are byte-identical
  to `6553afe`'s.
- **The future timestamps.**  All 16 B2 files carry mtime `2027-01-15T16:00:00`; my forced-rebuild
  touch set all 111 tracked `.rs` files to a future stamp as well, with content hashes asserted
  identical.  Nothing depends on wall-clock file time: the only `modified()` readers are the
  engine/hygiene/endpoint modules that look at *project artifacts*, not at the repository's own
  sources, and the only wall-clock assertions in the suite are the frame/read-timeout budgets, which
  measure elapsed durations rather than absolute time.

## 8. The B2 change table

| path | + | - | lines | sha256 |
|---|---|---|---|---|
| `.gitattributes` | 9 | 0 | 40 | `112f8caa…bf678` |
| `.spec/bevy/PRD.md` | 47 | 0 | 128 | `93b2ed85…4f8fbe` |
| `src/adapter/bevy/brp.rs` | 522 | 81 | 1230 | `37ce9337…b070c60` |
| `src/adapter/bevy/build.rs` | 559 | 12 | 724 | `e68f7749…9a6eeb6` |
| `src/adapter/bevy/contract.rs` | 109 | 10 | 501 | `fd5e5915…1e11d7c0f` |
| `src/adapter/bevy/mod.rs` | 1251 | 7 | 1256 | `21b6cb44…54785fa` |
| `src/adapter/mcp/evidence.rs` | 9 | 1 | 571 | `d09bf9f0…6202a0d02` |
| `src/adapter/mcp/generic.rs` | 23 | 0 | 682 | `2dd40e0d…84e8808` |
| `src/adapter/mcp/mod.rs` | 23 | 3 | 460 | `fc87a75c…c68c4088` |
| `src/adapter/mcp/semantic.rs` | 175 | 28 | 789 | `df127261…5c9ac878` |
| `src/adapter/mcp/server.rs` | 471 | 95 | 1181 | `e009d978…f626e01f` |
| `tests/bevy_adapter_b1.rs` | 11 | 1 | 258 | `1a9306b9…be86ad0f` |
| `src/adapter/bevy/battery.rs` (new) | - | - | 1071 | `b3f3bc60…53d6890688` |
| `src/adapter/bevy/launch.rs` (new) | - | - | 579 | `577912ba…f6a644b20d` |
| `src/adapter/bevy/prd.rs` (new) | - | - | 182 | `b2f7ad7b…dd1f056f` |
| `tests/bevy_adapter_b2.rs` (new) | - | - | 467 | `62707e9e…de8f050542` |

## 9. Independent judgement

The specification half of this batch is the strongest work I have checked in this track.  The
contract is genuinely a seventh surface, the tool hash genuinely covers the return shapes, and I
could reproduce **both** the old and the new values from the dumped documents rather than trusting
either number: removing this batch's delta from the new document reproduces the B1 pins exactly.
The PRD change is a model append-only change — byte-identical prefix, a measured length and hash,
an honest statement that no seal existed before, an attribute rule so the seal survives a checkout,
and a test that I made red myself by rewriting one character above the seal.  The battery really is
wired to the five observations, keeps raw calls per observation, and its jump criterion stays red
for a monotone fall.

The adapter half is not finished.  As shipped, a real round that uses the default reader with a
pinned lockfile would pay for the build and then fail `prepare()` with a contract violation that
lists all seven contract paths as missing, because the feature reader puts Bevy feature names into
the field `prepare()` checks as registered type paths; and with the default configuration it fails
even earlier, because nothing in production pins the lockfile the policy compares against.
`validate_artifact` constructs that default internally, so the E2 artifact gate cannot be green.
The budget is measured but not enforced, the feature-set check reads Bevy's declared feature table
rather than the resolved one, and one of the three D3 repairs would vanish without a single test
turning red.

I did not find a way to make the *old* D3 symptom return under the current tests: the mechanism the
B1 acceptance proved is pinned.  The weakness is the other direction — hardening that no test
holds in place.

## 10. Unverified and not checked

**Unverified (with reasons)**

1. A baseline full-suite run at HEAD: the additivity claim (`+63` passed, `+1` ignored) rests on the
   test-name diff and the counts, not on two measured runs.
2. **The forced rebuild**: fingerprints were cleared and all 111 tracked `.rs` files were touched
   with their content hashes asserted unchanged, but the rerun was still compiling when this report
   was written; its literal exit code and counts are deliberately not reported.
3. The two ignored real-machine smokes and any live-engine round (offline by order; no engine, no
   game, no 15702 listener on this machine).
4. The real `cargo build` + `cargo metadata` path end to end: `B2-1`/`B2-4` are established by
   composing the public functions on the documented metadata shape and by reading the source, not by
   building a real game.
5. Whether the D3 blocking repair is *necessary*: removing it changes nothing observable here.
6. SPIKE-1/SPIKE-2's own measurements; I only checked the code does not contradict them.
7. `+watch` streaming and any end-to-end round through `BevyMcpServer` against a real BRP endpoint.
8. The `WouldBlock` retry-to-deadline branch inside `fake::read_request`: no default-gate test
   stalls a request mid-body without closing, so I never saw that branch execute.

**What I did not check**

- `bevy_remote`'s own parameter schemas (the 23 generic tables are only checked against the declared
  table and SPIKE-1's names).
- The Godot battery's own assertions beyond running them in the gate.
- Windows socket semantics under sustained load: the D3 flakiness is a code-level reading plus the
  B1 acceptance's observed symptom, and my one attempt to reproduce it by removing the blocking call
  did not trigger it.

## 11. Advice for the next batch

1. **Take the missing report as the first item.**  With no `BATCH-B2-REPORT.md`, the next reader has
   no statement of intent, no change table, no gate numbers and no honesty section; they must
   reconstruct the batch from a 3209-line diff, and the one thing they cannot reconstruct is what
   the implementer believed it had verified.
2. **Fix the real build path before anything else** (`B2-1`): pin the lockfile where the adapter is
   constructed (or make an unpinned policy a typed error instead of a build-time comparison against
   the empty string), and split `ResolvedFeatures` into `features` and `type_paths` so the feature
   reader stops handing feature names to `check_registered_type_paths`; then add one test that drives
   `prepare()` through the *real* reader with a fake `cargo metadata` document.
3. **Verify the resolved feature set, not the declared one** (`B2-4`): read
   `resolve.nodes[].features` for the bevy package id.
4. **Enforce the budget** (`B2-5`): make `CargoBuilder` honour `BuildRequest.timeout` (kill and
   report `build_budget_exceeded`) rather than only measuring afterwards.
5. **Pin or drop the D3 blocking repair** (`B2-2`): either a test that a stalled-then-completed
   request is still read, or a comment saying it is defensive.  Also point the b2 D3 test at the real
   in-process fake, or rename it so it does not claim to pin what it does not.
6. **Make the battery honest about a failed read mid-phase** (`B2-7`): a failed coin/win read should
   make the observation "not observed", not "never rose".
7. **Resolve the ⑤ dead branch** (`B2-8`): either let the pre-injection baseline decide, as the
   comment says, or delete the comment.
8. **Add the control window to the jump phase** if the intent is that the arc is evidence of a jump:
   sample the same window with no jump injected and require the arc to be absent.  That would close
   the "a game that never jumps still passes" hole without changing the PRD's wording.
9. **Commit by decision, not by reset.**  A reset-plus-recommit that replaces the revision an
   acceptance is anchored to makes the acceptance chain hard to audit even when the push is
   authorised; an ordinary commit on top of the accepted revision keeps `f100e2f` reachable.
