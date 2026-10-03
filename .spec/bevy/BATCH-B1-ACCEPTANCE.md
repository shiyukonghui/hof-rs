# BATCH-B1 ACCEPTANCE - the engine-neutral runtime surface, the frozen contract, the remote client, the two-layer tool surface, the evidence layout

- Date: 2026-10-04
- Acceptance agent: independent subagent, no prior context, no implementer conclusion
- Revised: accepted revision `f100e2f`; HEAD while measuring `5994841`
- Environment: offline, no engine, no game, no network; scratch tree and logs under `F:\b1-acc\`
- Deliverable: this file

## Machine-readable verdict

The block below is the output of a JSON serialiser (`F:\b1-acc\py\verdict.py`), re-read and parsed back before this file was written.

```json
{
  "verdict": "pass",
  "batch": "BATCH-B1",
  "revision_accepted": "f100e2f",
  "head_at_acceptance": "5994841",
  "notes": "Code measured at f100e2f. HEAD 5994841 differs only in DECISIONS.md and .spec/bevy/BATCH-B1-REPORT.md, so src/ and tests/ are byte-identical between them and the gate measurements remain valid for the batch.",
  "criteria": [
    {
      "id": "C1-legacy-behaviour",
      "pass": true,
      "evidence": "git diff d0a4805 f100e2f -- src/adapter/godot.rs = +116/-2 and consists of exactly two replaced `use` lines plus one appended `impl GameAdapter for GodotAdapter` block; the only deletions in the whole commit are those two imports; no existing method, constant or test body is touched; GodotAdapter has no inherent method named engine/prepare/start/stop/read/inject/wait_frames/health/validate_artifact, so method resolution and runtime behaviour are unchanged; validate_artifact calls developer_artifact_valid_in / developer_artifact_defects_in, the same predicates ProjectAdapter's own methods already call; the full gate (751 passed) includes every pre-existing test unchanged; the mechanical panic scan finds 0 panic-capable constructs in the batch's added production lines."
    },
    {
      "id": "C2-failure-semantics",
      "pass": true,
      "evidence": "Own probe: project('bevy_grounded', [empty query result]) -> ContractViolation naming the missing frozen player marker, while project('bevy_grounded', [a row with on_ground:false]) -> {\"grounded\":false,\"frame\":2}; absent and observed-false are therefore distinguishable. Trait level: Reading::not_observed has failed=true, value=null and a reason; Reading::observed(false) has failed=false; serde round-trips. Eleven tool calls on a server with no process (including bevy_health, an unknown tool, a wrong-typed argument and a null result) all return typed ToolErrors and none panics; bevy_health without a registered process is no_game_process, never alive:false. Task-level failures are typed AdapterError variants, and EndpointTimeout classifies as infrastructure_failure while ContractViolation does not."
    },
    {
      "id": "C3-remote-client",
      "pass": true,
      "evidence": "endpoint() and BrpClient::local both give http://127.0.0.1:15702/; '15703' appears nowhere in the crate except two comments and one assertion, so there is no fallback path and the only way to address another port is BrpClient::new with an explicit string. Batching is unrepresentable: request_body always yields an object, a list-valued params payload is refused with InvalidRequest before the wire (probe: 0 requests sent), and an array reply is refused as Malformed. HTTP 200 with a non-null error body is a failure (repo test -32601 plus probe errors with string and missing codes -> BrpError::Rpc). Own attacks: a body truncated mid-body -> Malformed; two responses in one body -> Malformed; a reply whose id does not match the request -> accepted silently (defect D2); valid JSON of the wrong shape -> accepted as a null success (defect D1)."
    },
    {
      "id": "C4-pinned-surfaces",
      "pass": true,
      "evidence": "Independently recomputed with my own canonical-JSON + sha256 implementation: contract 4af153e77af87ceddb162c4b782701ee0b6c066a651d4e4b5d1e71f329649c69, tool list e177325fe8b2036c355d37b9373b85b524f4a7f0d999e087711366bca661ae97 and feature set d6a90ba39e67b9e05fd28d97cc570dc989a03e8ec7a15ba93d077d5fe95d1f96, all three equal to the pinned literals; the canonical form is stable when every object's keys are reversed (contract and tool list) and moves when one character changes; the tool list is 31 entries with rpc.discover first, schedule.graph 23rd, bevy_player_transform 24th and bevy_health last; all 23 generic tool names equal their BRP method names and the intersection with the 177-name Godot snapshot is empty. The semantic layer's five game paths and the engine Transform path all compare equal to contract entries (probe), but five of the six are duplicated literals bound to the contract only by a test (observation D4)."
    },
    {
      "id": "C5-gate",
      "pass": true,
      "evidence": "Clean full run: cargo test --offline literal exit code 0, 751 passed / 0 failed / 8 ignored / 759 listed over 63 result lines (log gate-full-3.log, gate-full-3.log.exit = 0). Forced rebuild (fingerprints cleared, all 111 tracked .rs files touched individually, log shows 'Compiling hof-rs'): exit 0, same 751/0/8/759. cargo fmt --all --check exit 0 with no output. The 8 ignored are the 7 pre-existing e0..e6 smokes plus the one deliberately ignored real-machine bevy_adapter_b1 test, which was never run. Four of the report's five plants re-run in a copy outside the repository each produced exactly the named red test (exit 101) and restored byte-identically, with green controls afterwards. No test was removed: the commit only adds lines except two imports, and the 99 added #[test] functions account for +93 lib and +5 passing integration tests plus the +1 ignore."
    },
    {
      "id": "C6-forbidden-zone",
      "pass": true,
      "evidence": "git status --porcelain is clean apart from the four pre-existing untracked JSON files; DECISIONS.md and the report differ from f100e2f only by the parent's own D297 commit, verified by git diff f100e2f --stat; Cargo.toml and Cargo.lock are unchanged in bytes and absent from the batch commit, and the new code uses only serde_json, thiserror, ureq, std and crate-internal paths, all pre-existing dependencies; the repository runs/ tree has the same 7341 entries before and after the full gate run (0 added, 0 removed) and no test writes below the repo runs/; branch master is ahead of origin/master by 3 and nothing was pushed; no rm -rf and no git checkout -- was used by me. The report's own machine-checkable artefact is its 12-row sha256 table, and all 12 values match the working tree exactly; there is no JSON verdict block in the report (defect D5)."
    }
  ],
  "defects": [
    {
      "id": "D1",
      "severity": "low",
      "what": "read_document accepts valid JSON that is not a JSON-RPC document as a successful null result. Only arrays are shape-checked; a number, a string, null, an empty object or an object with neither error nor result all return Ok(Value::Null), so a generic tool call reports ok:true with result null instead of Malformed.",
      "reproduction": "Own probe, src/adapter/bevy/brp.rs::read_reply/read_document: read_reply(\"42\") -> Ok(null); \"\\\"ok\\\"\" -> Ok(null); \"{}\" -> Ok(null); \"null\" -> Ok(null); '{\"jsonrpc\":\"2.0\",\"id\":1}' -> Ok(null); through the real wire on a raw loopback server BrpClient::call(\"world.list_resources\", None) on a body of '42' -> Ok(null). Contrast: '[]' and a batch array -> Malformed, and a body truncated mid-body -> Malformed. Not blocking: real BRP answers with an object, the semantic layer's project() turns a null into malformed_reply, and no green test or claim depends on the loose path. Suggested fix: require an object and an explicit `result` member (or reject anything that is not an object), returning Malformed otherwise."
    },
    {
      "id": "D2",
      "severity": "low",
      "what": "The JSON-RPC id of a reply is never compared with the id of the request that is waiting for it. A stale, duplicated, or out-of-order document is returned as the current call's result.",
      "reproduction": "Own probe: a raw loopback server answers the client's two requests (ids 1 and 2 on the wire) with two documents both carrying id 1; the second call returns {\"which\":\"stale\"} with no error. Not blocking: the client is blocking, uses one connection per call with Connection: close, and has no pipeline, so the real protocol cannot reorder replies; the exposure is a confused or hostile peer. Suggested fix: compare document[\"id\"] with the request id in call_document and return Malformed on a mismatch."
    },
    {
      "id": "D3",
      "severity": "medium",
      "what": "The in-process fake BRP server is load-sensitive, so the default gate can false-red. My first full cargo test --offline run on a fresh target directory exited 101 with two failures, both in adapter::mcp::server::tests: an_injection_writes_the_contract_field_and_reports_acceptance panicked unwrapping an empty recorded request body ('EOF while parsing a value') and an_unregistered_contract_type_is_a_contract_violation_not_a_zero saw kind 'transport' instead of 'contract_violation'. Six isolated cargo test --lib reruns and two later full runs were green.",
      "reproduction": "Run 1: CARGO_TARGET_DIR=F:/b1-acc/target-head cargo test --offline on a cold target while I was concurrently extracting a large git archive; literal exit code 101, 279 passed / 2 failed (log gate-full-1.log). Run 3 (idle machine) and the forced-rebuild run: exit 0, 751/0/8/759 (gate-full-3.log, gate-rebuild.log). Mechanism by construction: FakeBrp puts the listener in non-blocking mode and the accepted stream inherits it; read_request's `let _ = stream.set_read_timeout(...)` is ignored (on Windows a timeout on a non-blocking socket is rejected or disregarded), and every read error including WouldBlock becomes `return String::new()`, so the server can record an empty request and write/close its reply before the client's request bytes arrive - purely a scheduling race, not a fixed port or a shared listener. It is a defect in the test double, not in the product, and it did not block this verdict because two clean full runs reproduced the claim; it should be fixed next batch: set accepted streams back to blocking before reading, retry on WouldBlock until the header terminator or a real deadline, and make a failed request read fail the test instead of answering it."
    },
    {
      "id": "D4",
      "severity": "low",
      "what": "Five of the six semantic type paths are duplicated string literals in src/adapter/mcp/semantic.rs (PLAYER_PATH, GROUNDED_PATH, COIN_COUNTER_PATH, WIN_FLAG_PATH, INPUT_INTENT_PATH); only TRANSFORM_PATH aliases the contract's ENGINE_TRANSFORM_PATH. The module doc says the paths 'come from contract, never from a literal here', which is true for one of six. The binding to the contract is enforced by the test the_type_paths_used_by_the_layer_are_the_contracts_paths plus the pinned contract hash, not by construction.",
      "reproduction": "Read the constants at semantic.rs lines 34-44; my probe confirms each literal equals a contract entry (in_contract=true for all five) and that the test above is what ties them (a change to either side alone fails it, and a coordinated change also moves CONTRACT_SHA256). Not blocking: the test and the hash pin together make silent drift impossible; a future refactor could make them re-export the contract entries instead of restating them."
    },
    {
      "id": "D5",
      "severity": "low",
      "what": "The batch order asks for the report's machine-readable block to parse and round-trip; BATCH-B1-REPORT.md contains no JSON block (only two fenced status excerpts and a fenced directory tree). Its 12-row sha256 change table is the only machine-checkable artefact and it round-trips exactly. Separately, section 7 says the forced rebuild touched 101 tracked .rs files, but 101 is the baseline count at d0a4805; the batch revision f100e2f has 111 tracked .rs files.",
      "reproduction": "grep for fenced blocks in the report finds them at lines 287/296 and 376/381 only; no line starts with '{' or '['. git ls-tree -r d0a4805 --name-only | grep -c '\\.rs$' = 101, git ls-tree -r f100e2f ... = 111, git ls-files '*.rs' = 111. The under-touch does not invalidate the forced rebuild (the fingerprints were cleared and the log shows 'Compiling hof-rs'), but the number as written belongs to the baseline. Not blocking; documentation only."
    }
  ],
  "risks": [
    "D297 has already ruled that a seventh reflectable frame surface is added and that the semantic return shapes enter tools/list; both are contract changes, so CONTRACT_SHA256 and TOOL_LIST_SHA256 will move and B1's pinned literals must be re-pinned in the next batch. This is planned work, not a defect.",
    "The semantic layer's `frame` values are the adapter's observation ordinal, which D297 rejects as the frame source; the next batch changes that observable.",
    "The eight semantic return shapes are derived from SPIKE-1/SPIKE-2 live readings and were not re-measured against a real Bevy app in this batch.",
    "bevy_wait_frames waits 16 ms per frame on wall-clock time (SPIKE-2's 60.3 FPS), not on the game's own frames.",
    "D3 makes the default gate probabilistic under load; a CI runner under load can therefore report a false red on two socket tests.",
    "The ONE ignored real-machine smoke has never been executed, so its expectation (methodCount 23, version 0.19.1, server 15702) is unverified on this machine.",
    "The 23 generic parameter tables are only checked mechanically against the declared table and SPIKE-1's names, not against bevy_remote's own parameter schemas."
  ],
  "unverified": [
    "The ignored real-engine smoke test (no engine, no network offline).",
    "A baseline full-suite run at d0a4805: I did not run it, so 653/0/7/660 is taken from the report; I verified additivity instead (the commit only adds lines except two imports, and the 99 added #[test] functions explain +93 lib, +5 integration and +1 ignore).",
    "The +watch streaming paths (no SSE client test exists).",
    "Any end-to-end round through BevyMcpServer against a real BRP endpoint.",
    "SPIKE-1/SPIKE-2 measurements themselves (23 methods, 60.3 FPS, batch non-atomicity, the 2.04 s refused connect); I only checked that the code does not contradict them."
  ]
}
```

### How to read this verdict

- `verdict: pass` means the batch order's six jobs were each judged against
  evidence I produced myself; it does **not** mean "no defects" - five are
  filed, none blocking.
- The accepted revision is **`f100e2f`** for code and for the implementer's
  report. HEAD was **`5994841`** (the parent's D297 commit) while I measured;
  `git diff f100e2f --stat` touches only `DECISIONS.md` and
  `.spec/bevy/BATCH-B1-REPORT.md`, so `src/` and `tests/` are byte-identical
  between the two and the gate numbers below remain valid for the batch.
- Everything I ran is offline, on this machine, with no engine, no game and no
  network. My scratch tree, logs and scripts live under `F:\b1-acc\`
  (outside the repository); the repository itself was only read, except for
  this file.

## 1. Per-item table

| # | Job | Judgement | Evidence (all produced by me) |
|---|---|---|---|
| C1 | legacy adapter behaviour unchanged | **pass** | `git diff d0a4805 f100e2f -- src/adapter/godot.rs` is +116/-2: exactly two replaced `use` lines and one appended `impl GameAdapter for GodotAdapter` block; the commit's **only** two deletions in 5857 insertions are those imports; `grep "fn (engine|prepare|start|stop|read|inject|wait_frames|health|validate_artifact)" src/adapter/godot.rs` finds only the nine trait methods, so no inherent method is shadowed and behaviour cannot change; `validate_artifact` calls `developer_artifact_valid_in`/`developer_artifact_defects_in`, the same predicates `ProjectAdapter`'s methods already call (`godot.rs:5645`, `:5651`); a mechanical scan of the batch's added production lines finds 0 `unwrap()/expect/panic!/todo!/unimplemented!`; every pre-existing test still passes in the full gate |
| C2 | failure semantics, absent vs false, no panics | **pass** | below, section 3.1 - my own probe shows an absent subject is `ContractViolation` and a present-but-false subject is `{"grounded":false}`, and eleven tool calls return typed errors without panicking |
| C3 | remote client: endpoint, no batch, error-in-200, attacks | **pass** | below, section 3.2 - endpoint is `15702` with no fallback; batching is unrepresentable; an error body under HTTP 200 is a failure; three of my own attacks behave correctly (truncated body, doubled body, list params), two expose defects D1/D2 |
| C4 | two pinned surfaces | **pass** | below, section 3.3 - all three hashes recomputed independently with my own canonicaliser and SHA-256; reorder-stable and one-character-sensitive; 23 verb names = 23 method names with an empty intersection against the 177-name Godot snapshot |
| C5 | the gate | **pass** | `cargo test --offline` **literal exit code 0**, **751 passed / 0 failed / 8 ignored / 759 listed**, 63 result lines; the same numbers after a forced rebuild that logged `Compiling hof-rs`; `cargo fmt --all --check` exit 0; four of the five plants re-run (section 4) |
| C6 | nothing weakened, forbidden zone | **pass** | `runs/` has the same 7341 entries before and after the gate (0 added, 0 removed); `git status --porcelain` is clean apart from four pre-existing untracked JSON files; `DECISIONS.md` differs from `f100e2f` only by the parent's own D297; `Cargo.toml`/`Cargo.lock` unchanged and absent from the commit; `master` is ahead of `origin/master` by 3, nothing pushed; all 12 sha256 values in the report's change table match the working tree (defect D5 notes the missing JSON block) |

## 2. Gate evidence, stated as it stands

| Run | Command | Literal exit code | passed / failed / ignored / listed | Log |
|---|---|---|---|---|
| 1 (cold target, concurrent file I/O) | `cargo test --offline` | **101** | 279 / 2 / 0 / ... (lib terminated the run) | `F:\b1-acc\out\gate-full-1.log` |
| isolated lib reruns x6 | `cargo test --offline --lib` | **0** (x6) | 281 / 0 / 0 / 281 | `F:\b1-acc\out\librep.<n>.log` |
| 3 (idle machine, clean measurement) | `cargo test --offline` | **0** | **751 / 0 / 8 / 759** over 63 result lines | `F:\b1-acc\out\gate-full-3.log` |
| forced rebuild | clear `hof-rs-*` fingerprints, touch all 111 tracked `.rs` individually, then `cargo test --offline` | **0** | **751 / 0 / 8 / 759** | `F:\b1-acc\out\gate-rebuild.log` |
| format | `cargo fmt --all --check` | **0** | no output | `F:\b1-acc\out\fmt.log` |

- **The ignored count is explained**: 7 pre-existing `e0..e6` smokes plus the one
  new deliberately-ignored real-machine smoke
  (`tests/bevy_adapter_b1.rs::the_pinned_endpoint_answers_discover_with_the_23_methods_of_bevy_0191`,
  which demands a live Bevy on `127.0.0.1:15702` and was never run).
- **No test was removed.** The batch commit adds 5857 lines and deletes exactly
  two `use` lines; the 99 added `#[test]` functions account for +93 lib, +5
  passing integration tests and +1 ignore, i.e. 653 -> 751 passed and 7 -> 8
  ignored at the suite level.
- **No second test process of mine was running** during runs 3 and the forced
  rebuild (I checked `tasklist` before and after). During run 1 I was
  concurrently extracting a large `git archive`; that is disclosed because it is
  the load under which the two socket tests failed - see D3.
- **Forced rebuild:** `F:\b1-acc\out\force_rebuild.json` lists 111 touched
  files; the log contains `Compiling hof-rs v0.1.0 (F:\moonbit-hof-rs)`, so the
  binaries were genuinely rebuilt. Note that the report's section 7 says 101
  files; 101 is the baseline count (defect D5).

## 3. My own plants and counterexamples

### 3.1 Failure semantics (job 2)

Probe `probe_absent_versus_false` / `probe_no_method_panics`, run in a copy
outside the repository (`F:\b1-acc\out\probe.log`):

```
PROBE absent_subject ContractViolation("... no entity carries the frozen player marker `hof_game::contract::Player` ...")
PROBE present_false {"frame":2,"grounded":false}
PROBE distinguish_absent_from_false true
PROBE reading_missing failed=true value=null reason=true
PROBE reading_false failed=false value={"grounded":false}
PROBE reading_distinguishable true
PROBE reading_serde_roundtrip true
PROBE tool_kinds bevy_health=no_game_process bevy_wait_frames=ok bevy_inject_move=ok bevy_inject_jump=ok
  bevy_coin_counter=malformed_reply bevy_win_flag=malformed_reply bevy_player_transform=malformed_reply
  bevy_grounded=malformed_reply nope=unknown_tool world.get_resources=ok
  bevy_inject_move=invalid_arguments health_with_process={"alive":true,"stderr_tail":""}
```

A caller can therefore tell "not observed" from "observed false" on both
surfaces: the trait (`failed`/`value == null` plus a reason versus
`failed == false`) and the semantic layer (an error naming the missing marker
versus a projected boolean). Eleven calls, including the wrong-typed argument,
the unknown name and the null result, all came back as typed errors; none
panicked.

### 3.2 Remote client attacks (job 3)

Probe `probe_valid_json_wrong_shape`, `probe_id_correlation_and_out_of_order`,
`probe_connection_closes_mid_body`, `probe_two_responses_in_one_body`,
`probe_document_shapes_directly`, `probe_endpoint_identity`:

```
PROBE shape_number OK result=null            <- defect D1
PROBE shape_string OK result=null            <- defect D1
PROBE shape_empty_object OK result=null      <- defect D1
PROBE shape_no_result_no_error OK result=null<- defect D1
PROBE shape_null OK result=null              <- defect D1
PROBE shape_array_empty ERR variant=Malformed
PROBE shape_batch ERR variant=Malformed
PROBE wire_number OK result=null             <- defect D1, through the real wire
PROBE wire_no_result OK result=null          <- defect D1, through the real wire
PROBE truncated ERR variant=Malformed        <- correct
PROBE doubled ERR variant=Malformed          <- correct
PROBE id_first {"which":"first"}
PROBE id_second {"which":"stale"}            <- defect D2, id 2's reply was never checked
PROBE id_sent 1,2
PROBE list_params InvalidRequest requests=0
PROBE request_body_is_object true
PROBE endpoint http://127.0.0.1:15702/
PROBE local_client_endpoint http://127.0.0.1:15702/
PROBE explicit_15703 http://127.0.0.1:15703/
PROBE doc_error_string_code ERR variant=Rpc
PROBE doc_error_missing_message ERR variant=Rpc
PROBE doc_error_null OK result=7
PROBE doc_result_null OK result=null
```

`grep -rn 15703 src/` returns only two comments and one assertion, so no code
path can fall back to the render-world endpoint; the only way to address
another port is an explicit `BrpClient::new`. A list-valued `params` is refused
before the wire (0 requests seen by the server).

### 3.3 Pinned surfaces (job 4)

Independent recomputation, my own canonical JSON + SHA-256 (`F:\b1-acc\py\canon_check.py`),
run over a hand-transcribed contract table and over the tool list that the Rust
probe dumped:

```
PY_CONTRACT_SHA256   4af153e77af87ceddb162c4b782701ee0b6c066a651d4e4b5d1e71f329649c69
PY_TOOL_LIST_SHA256  e177325fe8b2036c355d37b9373b85b524f4a7f0d999e087711366bca661ae97
PY_FEATURE_SHA256    d6a90ba39e67b9e05fd28d97cc570dc989a03e8ec7a15ba93d077d5fe95d1f96
PY_CONTRACT_CHANGE_MOVES True       PY_CONTRACT_REORDERED_SAME True
PY_TOOL_MUTATED_MOVES True          PY_TOOL_REORDERED_SAME True
PY_TOOL_COUNT 31   PY_TOOL_FIRST rpc.discover   PY_TOOL_23RD schedule.graph
PY_TOOL_24TH bevy_player_transform  PY_TOOL_LAST bevy_health
```

All three equal the pinned literals. The canonicalisation is stable when every
object's keys are reversed (whole document for the tool list) and moves when a
single character changes. The semantic layer compares equal to the contract
(`in_contract=true` for all five game paths), and the 23 generic names equal
their BRP method names, with an **empty** intersection against the 177-name
Godot snapshot (`emit_old_vocab_overlap_count 0`). `entity_query` is neither a
Godot snapshot name nor a callable tool here; `world.query` is.

## 4. The plants I re-ran

Applied to a **copy** of `HEAD` under `F:\b1-acc\scratch-head` (never the
repository), each with a backup, a byte-equality assert after restore, and a
green control afterwards (`F:\b1-acc\run_plants.sh`, output in
`F:\b1-acc\out\plant-*.red.log`):

| # | File in the copy | Plant | Named test that went red (literal exit 101) | Restored sha256 == backup |
|---|---|---|---|---|
| P1 | `src/adapter/bevy/contract.rs` | `Grounded` -> `GroundedOnFloor` | `adapter::bevy::contract::tests::the_contract_hash_is_the_pinned_literal` | yes (`25ad1ddc...`) |
| P2 | `src/adapter/mcp/generic.rs` | tool name `world.query` -> `entity_query` | `adapter::mcp::tests::the_tool_list_hash_is_pinned_and_the_list_has_the_frozen_size` **and** `adapter::mcp::generic::tests::generic_tool_names_are_the_verb_names_verbatim` | yes (`ba684868...`) |
| P3 | `src/adapter/bevy/brp.rs` | disable the non-null `error` check in `read_document` | `adapter::bevy::brp::tests::an_error_body_under_http_200_is_a_tool_error` | yes (`6a438ead...`) |
| P5 | `src/adapter/godot.rs` | `read()` returns `Reading::observed(..., {"grounded": false})` | `the_legacy_godot_adapter_implements_the_capability_surface_without_panicking` (integration) | yes (`17a8a460...`) |
| - | control | pristine copy | `the_contract_hash_is_the_pinned_literal` **exit 0**; integration suite **exit 0, 5 passed / 1 ignored** with `Compiling hof-rs` | - |

**Method note (a reversed reading I caught).** My first control run of the
integration suite after P5 was **red** even though the source had been restored
byte-identically. The cause was my own restore timestamp: I stamped the
restored file *in the past* (`1_791_000_000`, i.e. the previous day), which is
older than the just-built fingerprint, so cargo kept the binary compiled from
the planted source. I fixed the restore to stamp `now + 30 s`, re-ran, and got
`Compiling hof-rs` followed by exit 0. This is exactly the stale-binary hazard
the batch order warns about, and it is why every plant table above also lists a
control.

### 4.1 Discrepancies found while running the plants

- The report says the forced rebuild touched **101** tracked `.rs` files; the
  batch revision has **111** (`git ls-tree -r f100e2f`), while `d0a4805` has
  101. The force still rebuilt (fingerprints were cleared), so the claim's
  substance holds and only the number is wrong (D5).

## 5. Independent judgement

The batch does what the order says, and the strong parts are strong for the
right reason: the contract and the tool list are pinned by hashes that I could
recompute from an independent implementation, the failure semantics really do
let a caller separate "not observed" from "observed false", the client cannot
batch and cannot reach 15703, and the legacy adapter's change is genuinely
confined to an `impl` block plus two imports.

The weaknesses are boundary conditions, not headline claims. The client trusts
the shape of the body (D1) and the identity of the reply (D2); the fake server
that most client tests rely on is timing-dependent by construction (D3); five
contract paths are restated as literals and held in place by a test rather than
by construction (D4); and the report's own machine-readable surface is a hash
table, not the JSON block the order asks for (D5). None of these blocks the
batch, because two clean full runs reproduce the claim, every defect has an
explicit reproduction, and each fix is local.

I did **not** find a way to make the legacy path change behaviour: no
trait method is called anywhere in `runtime/**` or `adapter/**` yet, no
inherent method is shadowed, and `validate_artifact` reuses the existing
predicates verbatim.

## 6. Unverified and not checked

**Unverified (with reasons)**

1. The ignored real-engine smoke - no engine, no network, offline by order.
2. A baseline full-suite run at `d0a4805`: I did not run it, so
   `653 / 0 / 7 / 660` is the report's number; I verified additivity instead.
3. The `+watch` streaming paths: no SSE client test exists in the batch.
4. Any end-to-end round through `BevyMcpServer` against a real BRP endpoint.
5. SPIKE-1/SPIKE-2's own measurements; I only checked the code does not
   contradict them, and did not re-measure 23 methods, 60.3 FPS, batch
   non-atomicity, or the 2.04 s refused connect.

**What I did not check**

- `bevy_remote`'s own parameter schemas: the 23 parameter tables are only
  checked mechanically against the declared table and SPIKE-1's names.
- The real evidence-writing round (`runs/bevy-<round>/` with a live game).
- The Godot battery's own assertions beyond running them in the gate.
- Windows-specific non-blocking socket semantics I could not exercise directly
  (the D3 mechanism is a code-level reading plus the observed symptom, not a
  syscall trace).

## 7. Advice for the next batch

1. **Re-pin the frozen surfaces.** D297 adds a seventh reflectable frame
   surface and puts the semantic return shapes into `tools/list`; both move
   `CONTRACT_SHA256` and `TOOL_LIST_SHA256`. Do it deliberately, in one change,
   with the new literals and the decision entry, and expect B1's pins to go red
   first.
2. **Fix the fake server before it is trusted with more tests** (D3): set
   accepted streams back to blocking, retry on `WouldBlock`, honour a real
   deadline, and fail the test when the request read fails instead of answering
   a request that was never read. A gate that can false-red under load is worse
   than a slow one.
3. **Tighten `read_document`** (D1/D2): require an object, require the `result`
   member for a request/reply call, and compare the reply `id` with the request
   `id`; return `Malformed` otherwise. Both are small and both remove silent
   degradation.
4. **Make the semantic layer re-export the contract entries** instead of
   restating five paths (D4), so the binding is structural rather than
   test-enforced.
5. **Run the ignored smoke once** on a machine with a live Bevy on 15702 and
   record the raw `rpc.discover` document as evidence; it is the only check of
   the endpoint/version/23-method claim.
6. **Give the report a real machine-readable block** (D5), generated by a
   serialiser like this one, so the next acceptance can parse it instead of
   scraping tables.
7. **Keep the two-target discipline** for gate measurements, and stamp restored
   files strictly *after* the build that used the planted copy - the failure I
   hit is silent and reverses a verdict.

## 8. Disclosure: the report revision

I read and hashed `.spec/bevy/BATCH-B1-REPORT.md` as committed in `f100e2f`
(`a4ecf418233a8476af553cd25ee8ae9e155366c5cc9756b198745ea4eac0bc24`) before the
parent's D297 commit amended it to
`1d9c8a400bc3dd651225fd995a3d87725399ce158dae1ae110b8a479e6f5dc8e` (+71/-27).
The amendment is a numbers/clarity revision plus a note that the parent
committed the batch during the implementation; it does not touch code. All 12
sha256 values in its change table still match the working tree, so the
amendment did not change any artefact I measured. I have anchored every code
claim to `f100e2f`.
