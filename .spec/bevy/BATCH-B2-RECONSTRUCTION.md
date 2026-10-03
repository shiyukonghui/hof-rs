# BATCH-B2 RECONSTRUCTION — what the second Bevy adapter batch actually did

> **This is a reconstruction, not the implementer's account.**  BATCH-B2 was
> landed without `BATCH-B2-REPORT.md`: the implementer never wrote one.  What
> follows was reconstructed by the BATCH-B3 implementer from the working tree,
> the diff against the last accepted revision (`6553afe`), and
> `.spec/bevy/BATCH-B2-ACCEPTANCE.md`.  It records **what the bytes do**, and it
> deliberately says nothing about what the implementer believed it had verified,
> because that is exactly the part that cannot be recovered.

## 1. Revision and shape

- Base revision: `6553afe` (`feat(bevy): add the engine-neutral adapter trait,
  the frozen contract, the remote client and the two-layer tool surface`), which
  is what `origin/master` was at when B2 ran.
- B2 landed **uncommitted**: 12 tracked files modified, 4 new files, 16 in total.
- The acceptance of B2 is `.spec/bevy/BATCH-B2-ACCEPTANCE.md` (verdict `fail`),
  committed afterwards as `fca7647`.  B2 itself was never committed as its own
  revision before B3 started.

## 2. Change table (as measured by `git diff --stat HEAD`, B2 tree)

| path | change | note |
|---|---|---|
| `src/adapter/bevy/mod.rs` | +1251 / −7 | `BevyAdapter` body: `GameAdapter` impl, evidence recording, `StaticFeatures` |
| `src/adapter/bevy/build.rs` | +559 / −12 | `CargoBuilder`, `FeatureReader`/`CargoMetadataFeatures`, `FakeBuilder`/`FakeFeatures`, budgets |
| `src/adapter/bevy/brp.rs` | +522 / −81 | strict reply shape (D1), id correlation (D2), deterministic in-process fake (D3) |
| `src/adapter/mcp/server.rs` | +471 / −95 | frame-counter-first reads, frame wait on the game's counter |
| `src/adapter/mcp/semantic.rs` | +175 / −28 | `outputSchema` per semantic tool, `frame_read_plan`, `project_game_frame` |
| `src/adapter/bevy/contract.rs` | +109 / −10 | seventh surface `frame_counter`, re-pinned hash |
| `.spec/bevy/PRD.md` | +47 / −0 | append-only appendix B2 (seventh surface, `hof_game`, output schemas) |
| `.gitattributes` | +9 / −0 | `.spec/bevy/PRD.md -text` so the seal survives a checkout |
| `src/adapter/mcp/generic.rs` | +23 / −0 | (no semantic change; schema plumbing) |
| `src/adapter/mcp/mod.rs` | +23 / −3 | `ToolSpec::output_schema` into `tools/list` |
| `src/adapter/mcp/evidence.rs` | +9 / −1 | frame counter in the evidence path |
| `tests/bevy_adapter_b1.rs` | +11 / −1 | follow the seventh surface and the re-pinned hash |
| `src/adapter/bevy/battery.rs` (new) | 1071 lines | the five E3 observations |
| `src/adapter/bevy/launch.rs` (new) | 579 lines | same-binary headless launch, readiness, stop |
| `src/adapter/bevy/prd.rs` (new) | 182 lines | PRD sealed-prefix verification |
| `tests/bevy_adapter_b2.rs` (new) | 467 lines | cross-module pins (hashes, seal, D1–D4) |

Totals: **3209 insertions, 238 deletions** over 12 tracked files, plus 4 new
files.

## 3. The two frozen surfaces B2 moved

| surface | B1 value | B2 value |
|---|---|---|
| `sha256(canonical_json(CONTRACT))` | `4af153e77af87ceddb162c4b782701ee0b6c066a651d4e4b5d1e71f329649c69` | `792001e7e629ccc25d6c486eeb54360d83ffb208befa4ca5e430c6f0e747f4f9` |
| `sha256(canonical_json(tools/list))` | `e177325fe8b2036c355d37b9373b85b524f4a7f0d999e087711366bca661ae97` | `bcf03c0b06295cfd27cc0359a7fa272ed435bdf61525d67b08981c62d30e43b1` |
| feature set (unchanged) | `d6a90ba39e67b9e05fd28d97cc570dc989a03e8ec7a15ba93d077d5fe95d1f96` | same |

The delta is exactly what the acceptance reproduced independently: one
`frame_counter` contract entry and eight `outputSchema` members.

## 4. What the acceptance found (the reason B3 exists)

The acceptance verdict was `fail`.  Its twelve defects are restated, with the
B3 status, in `BATCH-B3-REPORT.md`.  In reconstruction terms, the B2 bytes
contained:

- a `prepare()` whose default build policy was **unpinned** (`lock_sha256:
  String::new()`), and which fed the **feature reader's feature-name list** into
  `check_registered_type_paths` — so the real path could not succeed;
- a feature reader that read the **declared** feature table
  (`packages[].features`) rather than the resolved set;
- a `CargoBuilder` that never read `BuildRequest.timeout` and blocked in
  `wait_with_output`;
- a launch path whose readiness probe could only use 15702 while the adapter set
  an environment override for another endpoint;
- a battery that dropped a failed coin/win read from the series and reported the
  drop as a measured failure;
- a dead branch in the jump phase's grounded criterion;
- an id check that accepted a reply carrying no `id` member;
- a "by construction" path pin whose assertion was true by definition;
- a D3 test that exercised a server defined inside the test file rather than the
  in-process fake; and
- one dead-code warning (`brp::fake::malformed_request_reply`).

## 5. What cannot be reconstructed

- **Intent.**  There is no statement of what B2's implementer believed, which
  parts it had verified, or which parts it considered unfinished.  The code and
  the acceptance are the only evidence.
- **The gate's forced-rebuild numbers.**  The acceptance recorded that its
  forced rebuild had not finished when it wrote its report, so no B2
  forced-rebuild exit code exists to compare against.
- **The D3 "blocking restore" necessity.**  The acceptance could not make the
  symptom return by removing the repair, so whether the repair is load-bearing
  on Windows is still unproven; B3 pins its presence rather than proving its
  necessity.
