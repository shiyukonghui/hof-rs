```json
{
 "schema": "hof-rs / bevy round-2 independent acceptance of the round-1 PRD-coverage and evidence-reproducibility batch",
 "produced_at": "2026-10-05",
 "branch": "bevy-core",
 "head_under_acceptance": "201af0a (the batch's own commit; parent 5f526d2)",
 "working_tree": "CLEAN at HEAD 201af0a (`git status --porcelain` empty) before and after this acceptance, except this report, which is the deliverable",
 "verdict": "fail",
 "reproducibility_passes": false,
 "decidability_passes": true,
 "cost_criterion_passes": false,
 "cost_ratio_to_target": 2.4341,
 "headline": "The decidability repair is real and I reproduced it: coverage is now a function of 19 stable ids whose literal anchors I found in the frozen PRD, the denominator cannot move with the Tester, and the recorded round scores exactly 13 verified / 2 gap / 4 unobservable. D-1 is restated correctly (my own replay: live K=43 aborts at call 87 and cuts the call-95 write; K=51 aborts at 95; K=52 aborts at 96 and cuts nothing; 37 < 43 < 52). The gate on the working tree is exactly the reported one (exit 0, 800/0/6/806, 0 warnings, fmt exit 0, 18 tests added, 0 removed), the add is key-clean, the frozen documents are byte-untouched and DECISIONS.md is append-only. BUT the batch's own reproducibility claim fails on its own machine: a FRESH `git clone` (no runs/**) checks the evidence corpus out with CRLF because `core.autocrlf=true` and nothing in .gitattributes pins `evidence/**`, so `cost.trajectories_total_bytes` becomes 4,197,568 instead of 4,166,273 and TWO committed tests (`tests/evidence_reproduction.rs::the_committed_cost_corpus_is_the_recorded_one` and `::the_evidence_index_names_committed_files_and_commands`) fail in the clone. A clone's gate is red. The numeric analysis itself does reproduce from the repository (write_accounting 7/7 and prd_coverage 5/5 pass in the clone), so the defect is narrow, precise and one line to fix - but it is exactly the defect the batch existed to close.",
 "criteria": [
  {
   "id": "C1-reproducibility",
   "pass": false,
   "evidence": "Working tree: every one of the index's cost, write-accounting, band, coverage and observation headlines reproduced byte-for-byte by my own scripts reading ONLY evidence/** (D:/hof-acc9-work/repro.py, coverage_check.py, rawcalls.py, identity.py). Fresh clone: `git clone /f/moonbit-hof-rs D:/hof-acc9-clone` (316 tracked files, no runs/ dir) then `cargo test --offline --no-fail-fast --test evidence_reproduction --test write_accounting --test prd_coverage` in D:/hof-acc9-clone-target -> exit 101; evidence_reproduction 5 passed / 2 FAILED; write_accounting 7 passed; prd_coverage 5 passed. The two failures are byte-count assertions broken by git's LF->CRLF checkout conversion (core.autocrlf=true, .gitattributes pins only .githooks/**, scripts/*.sh and .spec/bevy/PRD.md). 16 of the 18 index headlines reproduce from a clone; `cost.trajectories_total_bytes` does not, and `gate.counts_at_the_start_tree` never could (see E-6)."
  },
  {
   "id": "C2-no-key-shaped-material",
   "pass": true,
   "evidence": "My own transcription of src/runtime/secrets.rs (KEY_PREFIXES/KEY_BODY_MINIMUM=16 / KEY_ASSIGNMENT_NAMES/KEY_VALUE_MINIMUM=32) plus a broader vendor regex, run over all 139 files the batch commit touched: no repo-rule finding at all (D:/hof-acc9-work/keyscan_mine.py). The only broad-regex hit is the literal `sk-late-occurrence` inside evidence/tools/keyscan.py's own ALLOWED list. Positive control fires: the scanner reports `sk-bbb...` (24 body chars) and `looks_key_shaped=True` on a synthetic key. keyscan.py is a faithful transcription (its ALLOWED list is byte-identical to tests/credential_scan.rs's ALLOWED_PLACEHOLDERS, and both entries are below the 16/32 thresholds so the allowlist hides nothing); it prints fingerprints and lengths, never values. build_evidence.py refuses a key-shaped file before writing it. The repository's own scan test excludes only {.git, target, .workspace, runs, node_modules}, so it really does cover evidence/."
  },
  {
   "id": "C3-decidability",
   "pass": true,
   "evidence": "19 ids in src/adapter/bevy/prd_surfaces.rs::PRD_SURFACES; I recomputed all 19 literal anchors against the frozen .spec/bevy/PRD.md and every one is present (Q-not-required occurs twice, the rest once). P1..P5, C1..C6 and B2.1..B2.4 are the document's own labels; Q-scale/Q-startup/Q-not-required/Q-perf are harness-coined names for the four bolded §4 clauses, each anchored to that clause's literal title. The set is not selected by observability - four of the 19 are Unobservable and are included anyway. Scoring the committed evidence/observation/round4/deterministic/battery.json with my own implementation of the deciders gives exactly 13 verified / 2 gap (Q-startup, B2.1) / 4 unobservable of 19, and 15/0/4 for a ten-step battery. The denominator cannot move with the Tester (decide() reads only step outcomes; tests/prd_coverage.rs::the_surface_denominator_does_not_move_with_the_testers_claims pins it). Frozen documents byte-identical between 5f526d2 and 201af0a (PRD.md, REQUIREMENTS.md, DESIGN-OVERVIEW.md, DESIGN-DETAIL.md, both acceptances, ROUND-4-REPORT, COST-REPORT, FIX-REPORT, both spikes, config/hoh.yaml)."
  },
  {
   "id": "C4-d1-restated",
   "pass": true,
   "evidence": "My own replay of the withdrawn rule over the committed trajectories: live call K=43 -> abort at call 87 (1,651,225 tokens) with project_writes_after = [95]; K=50 -> abort 94 with [95]; K=51 -> abort 95 and the write never happens (empty after-list); K=52 -> abort 96 and nothing recorded is cut. Round-4 iter-3 never fires at K=43 and at K=42 aborts at 49 cutting the seven real edits at 75..98. Last cumulative under 1,500,000 on the live call is call 81 (1,484,934), call 82 = 1,511,382, so K <= 37. Hence 37 < 43 < 52, with 51 under the strict `> abort` convention. The restatement is in both machine blocks and both proses, quotes the old `K >= 43` wording rather than erasing it, is in DECISIONS.md D305, and is pinned by tests/write_accounting.rs::the_global_safe_floor_is_fifty_two_and_not_forty_three and ::the_two_bands_do_not_overlap (both names exist)."
  },
  {
   "id": "C5-gate",
   "pass": true,
   "evidence": "Free space checked first (D: 252 G, F: 57 G, nothing deleted). Own build directory D:/hof-acc9-target (9.1 G): `cargo test --offline` literal exit code 0 -> 800 passed / 0 failed / 6 ignored / 806 listed over 60 `test result:` lines; `cargo test --offline -- --list` exit 0 with 806 names; `-- --list --ignored` exit 0 with the same six real-engine names as the report lists, all present in the full list; `cargo fmt --all --check` exit 0 emitting 0 bytes; 0 `warning:` lines (`grep -c warning:` = 0; the five 'warning' strings are test names). No test removed: `git diff 5f526d2 201af0a -- src tests` adds 18 `#[test]`/`#[tokio::test]` attributes and removes 0, and 05604b9->5f526d2 is a docs-only commit, so the 788 baseline holds and 788+18=806. No cargo/rustc/hoh process before or after. The clone gate is the separate failure in E-1."
  },
  {
   "id": "C6-tree-coherence",
   "pass": true,
   "evidence": "316 tracked files, top-level entries only .gitattributes/.githooks/.gitignore/.spec/Cargo.lock/Cargo.toml/DECISIONS.md/config/evidence/scripts/src/tests; `git ls-files runs` is empty. DECISIONS.md is append-only across the batch commit (1295073 -> 1306821 bytes, the old bytes a byte prefix of the new file, +11748 = D305). The round-4 launch ledger holds 7 launches with 7 distinct nonces, pids and launch images, and its last line (nonce faf2adda-c698-48ef-a4f5-f51d1da551c6, pid 47624, port 15702) is the launch meta.json and launch.json report as verified. Identity, tripwire, fold and resume logic are green in the gate. HEAD 201af0a is NOT origin/bevy-core (5f526d2): nothing is pushed. The cost criterion is still unmet at 2.434x and is recorded as unmet."
  }
 ],
 "defects": [
  {
   "id": "E-1",
   "severity": "high",
   "what": "The evidence corpus is not byte-stable across a checkout, so the batch's reproducibility claim fails in a clone and a clone's gate is red. `core.autocrlf=true` on this machine (the project's own .gitattributes comment says so) and no .gitattributes rule covers `evidence/**`, so every LF in the committed text files becomes CRLF on checkout. Measured: livecost1 1,041,144 -> 1,052,155; round4-iter-1 602,673 -> 607,159; iter-2 1,786,110 -> 1,794,665; iter-3 736,346 -> 743,589 (+1 byte per newline; identical after CR removal, so the JSON parses and the numeric analysis is unaffected). `cost.trajectories_total_bytes` 4,166,273 -> 4,197,568. index.json corpus bytes 4,771,139 -> 4,827,317. index.json and README.md themselves grow by 222 and 65 bytes, and DECISIONS.md by 11,613. PRD.md is pinned `-text` and does not move, so the seal is safe - the trap the project already solved once was left unpinned for the new corpus.",
   "reproduction": "`git clone /f/moonbit-hof-rs D:/hof-acc9-clone` (316 files, no runs/), then in the clone `CARGO_TARGET_DIR=D:/hof-acc9-clone-target cargo test --offline --no-fail-fast --test evidence_reproduction --test write_accounting --test prd_coverage` -> exit 101; evidence_reproduction 5 passed / 2 FAILED with `the four trajectories' own bytes left 4197568 right 4166273` and `the index's byte count must be the corpus that is here left Some(4771139) right Some(4827317)`; write_accounting 7 passed; prd_coverage 5 passed. Logs D:/hof-acc9-work/clone_test2.out, D:/hof-acc9-work/crlf.py. Remedy (NOT applied): pin `evidence/** -text` in .gitattributes."
  },
  {
   "id": "E-2",
   "severity": "medium",
   "what": "`S1-deterministic-step` is published as CLOSED 'by a real observation, not by loosening the definition', but no observation of it has ever been produced. The tenth battery step `e3_process_liveness` exists, is wired into E3_STEPS, has a real FrameAdvance verdict and is unit/fake-driver tested, but there is no committed `.hoh/deterministic/raw/e3_process_liveness.json` (raw/ holds 11 files, none of them liveness), no round has ever run the ten-step battery, and the batch's own `unverified` list says the step 'has never executed against a real game'. The disposition in src/adapter/bevy/prd_surfaces.rs::RESIDUALS carries the same overclaim in shipped code.",
   "reproduction": "`ls evidence/observation/round4/deterministic/raw` -> 11 files, no e3_process_liveness.json; the bundle's `unverified[0]` in .spec/bevy/COVERAGE-EVIDENCE-REPORT.md says the live path has never run. Correct wording: 'implemented and unit-tested; pending its first real observation'. This does not change the recorded 13/19 figure."
  },
  {
   "id": "E-3",
   "severity": "low",
   "what": "The batch states that the frozen contract declares 'eight' reflectable semantic surfaces and that a goal surface would be a 'ninth'. The frozen PRD declares SEVEN (six rows in §3-C2 plus the frame counter added by 附录 B2.1, whose own heading is '第七个可反射语义面'). The same sentence says B2.1 'took it from six surfaces to seven' before calling the result eight.",
   "reproduction": "I counted the §3-C2 table data rows (6) and B2.1's addition (1) in .spec/bevy/PRD.md. The wrong count appears at COVERAGE-EVIDENCE-REPORT.md line 254 (JSON block), line 687 (prose) and src/adapter/bevy/prd_surfaces.rs line 278. No registry item or verdict depends on it - the goal is absent from 6, 7 or 8 alike."
  },
  {
   "id": "E-4",
   "severity": "low",
   "what": "The report says evidence/index.json 'states, for each of 14 headline numbers' and 'carries 14 headline entries'; the file carries 18, and the batch's own test asserts `headlines.len() >= 15`.",
   "reproduction": "`python -c` over evidence/index.json (D:/hof-acc9-work/tree_check.py) prints 18 entries; the wrong count is at COVERAGE-EVIDENCE-REPORT.md lines 612 and 742."
  },
  {
   "id": "E-5",
   "severity": "low",
   "what": "index.json describes `observation.round4.raw_calls` as 'the raw MCP->BRP exchanges ... one JSON-RPC request per file'. Each of the 57 files carries 2 or 3 JSON-RPC sub-requests (histogram: 44 files with 2, 13 with 3), all reusing the call's own sequence id - which is the correct property, and the report's prose states it correctly ('one semantic call each, no batch'). The entry also names a directory, not files, so the index's own 'every path here is tracked' test accepts it via `path.exists()`.",
   "reproduction": "D:/hof-acc9-work/rawcalls.py: requests-per-file histogram {2: 44, 3: 13}; widest file 0002-bevy_wait_frames.json has ids [2,2,2] and methods ['world.get_resources' x3]."
  },
  {
   "id": "E-6",
   "severity": "low",
   "what": "index.json marks `gate.counts_at_the_start_tree` (782/0/6/788) `repo_independent: true` with the command `cargo test --offline -- --list`. It is a historical measurement transcribed into .spec/bevy/ACCEPTANCE-ACCOUNTING.md; the named command on this tree returns 806 names, not 788. Nothing in the index reproduces 788.",
   "reproduction": "cargo test --offline -- --list gives 806 names in the working tree; the value's only 'file' is the acceptance document that asserts it."
  },
  {
   "id": "E-7",
   "severity": "low",
   "what": "The corpus total '118 files / 4,771,139 bytes' excludes evidence/index.json, evidence/README.md and the two tools, which are themselves committed under evidence/. The directory really holds 122 files / 4,796,132 bytes. README's own table gives that group as '3' files when there are 4 (index, README, build_evidence.py, keyscan.py), and its total row sits below that group row without saying the group is excluded. The repository test defines the corpus as the 118 deliberately, so this is a wording inconsistency rather than a false number - but the report's phrase 'evidence/ is 118 files' is wrong taken literally.",
   "reproduction": "D:/hof-acc9-work/census.py: 122 files / 4,796,132 bytes; the 118 = the six data groups; index+README+tools = 4 files / 24,993 bytes."
  }
 ],
 "risks": [
  {
   "id": "R-1",
   "risk": "The liveness step may fail on a real game. `e3_process_liveness` has never run; if the game's reported frame counter lags the requested wait, Q-startup and B2.1 come back red and the 15/19 projection becomes 13/19 with two honest gaps.",
   "why_it_matters": "It is the one thing a green gate does not prove, and it decides two of the nineteen surfaces."
  },
  {
   "id": "R-2",
   "risk": "The cost criterion is still unmet: 3,651,120 total tokens on the one live Developer call = 2.434x the 1,500,000 target, and the corrected accounting makes the withdrawn lever's damage larger (K >= 52 rather than 43).",
   "why_it_matters": "One of the goal's five criteria remains open, and only one iteration-1 call has ever been measured."
  },
  {
   "id": "R-3",
   "risk": "Every conclusion outside the four committed trajectories still rests on the gitignored runs/** (the other roles, rounds 1-3 and the five round-4 attempts), and the corpus is a copy whose byte-faithfulness to runs/** cannot be re-verified from the repository.",
   "why_it_matters": "R-2 of the previous acceptance is only partly answered, and E-1 shows the answer is even weaker than claimed."
  },
  {
   "id": "R-4",
   "risk": "Two published numbers have no committed evidence and appear in neither unreproducible list: the redaction sidecars' 187/180/180/977-byte deltas with '12 occurrences', and the claim that the committed corpus is a faithful subset of runs/**.",
   "why_it_matters": "The 'what cannot be reproduced' list is not exhaustive, which is the same class of gap the batch was closing."
  },
  {
   "id": "R-5",
   "risk": "The repository's stale 'PRD's functional requirement ids are F1..F17' framing (src/model.rs:246, and the CLI line's total_is_known branch) does not correspond to any F-id in the frozen PRD.md, which has none.",
   "why_it_matters": "Pre-existing rather than introduced here, but it is the conceptual root of RA-5 and is still the fallback denominator."
  }
 ],
 "unverified": [
  "The contents of the gitignored runs/** tree (11,229 files / 11.898 GiB as reported): I did not read or measure it, by instruction, so I cannot confirm the corpus is a faithful subset of it.",
  "Whether a Linux/macOS clone (core.autocrlf=false) passes. The mechanism says it would, because the committed blobs are LF; I ran only the Windows clone on this machine.",
  "The lever pairs and the compact_history projections: not re-derived.",
  "Byte-level identity of what a successful shell write put on disk: the recording proves a write ran and reported success, not that the bytes changed.",
  "That the committed evidence_reproduction test's other five tests would still pass on a machine with different line-ending settings - they do here and in the clone."
 ],
 "single_most_important_thing_next_batch": "Add `evidence/** -text` (and consider `*.json -text`) to .gitattributes, then re-run the clone check: `git clone` a fresh copy and `cargo test --offline` inside it. Until a clone's gate is green, the repository does not carry its own evidence. Then run ONE live round and read `result.json.prd_coverage.surfaces`; expect 15/19 with four named unobservable items, and treat a red Q-startup/B2.1 as the liveness step failing honestly. Restate S1 as 'implemented, pending its first real observation' rather than 'closed'."
}
```

# ACCEPTANCE-EVIDENCE — independent acceptance of the PRD-coverage and evidence-reproducibility batch

Independent, **offline** acceptance of `bevy-core` at **`201af0a`**. No engine, no game, no
network, no model call, no round and no Developer call was run. I did not write under
`runs/**`, did not construct a path from an unexpanded variable, did not use `git checkout --`,
did not use `rm -rf` or a wildcard deletion, did not commit, stage or push, and did not fix
anything. The working tree was clean at HEAD before and after; the only file I wrote inside the
repository is this report. Every helper script lives outside it, under `D:/hof-acc9-work/`, and
every tampering experiment (the clone) lives outside it too. No existing file was modified, so no
timestamp/backup restoration was needed.

The machine-readable verdict is the first thing in this file. It is `json.dumps(..., indent=1,
ensure_ascii=False)` output written by `D:/hof-acc9-work/write_report.py` and then **parsed back
out of this written file**; the parse is the last thing the generator does and it fails if the
block does not round-trip.

## 0. The verdict in one paragraph

**Reproducibility fails; decidability passes.** In the working tree I reproduced every one of the
index's 18 headlines from `evidence/**` alone, with my own scripts and my own re-implementation of
the write-accounting grammar — the cost totals, all four write profiles, the K=32 replay, the three
band edges including the corrected **K ≥ 52**, the 19-item registry and the recorded **13/19**, the
eleven battery records, the 57 raw calls and the Tester's self-referential 6/8. D-1's restatement is
correct and the non-overlap conclusion holds and is stronger. But the batch's own test of its own
claim fails where it matters: a **fresh `git clone`** checks the corpus out with CRLF
(`core.autocrlf=true`, nothing pins `evidence/**`), so `cost.trajectories_total_bytes` is 4,197,568
instead of 4,166,273 and **two committed tests fail in the clone** — the clone's gate is red. That
is precisely the defect class the batch existed to close, the project has already solved it once
for `PRD.md`, and it is one `.gitattributes` line to fix. The numeric analysis does survive a clone
(`write_accounting` 7/7 and `prd_coverage` 5/5 pass there), so the failure is narrow — but a tree
whose own suite is red on a clean checkout must not be authorised to push as "reproducible from the
repository".

## 1. What I did, and with what

* I read the whole relevant record first: the batch report, the acceptance that passed and its D-1,
  the write-accounting report, `ROUND-4-REPORT-COMPLETE.md`, the frozen `PRD.md` and
  `REQUIREMENTS.md`, `DECISIONS.md`, `evidence/README.md`, `evidence/index.json`, and the code under
  `src/` and `tests/` the batch touched.
* I wrote my own accounting from scratch in `D:/hof-acc9-work/repro.py`: my own directive parser, my
  own shell/PowerShell/Python write detector, my own return-code pairing, my own replay of the
  withdrawn rule. It shares no code with `src/harness/write_audit.rs`. It reproduces every published
  timeline and every published K number.
* I re-implemented the 19 deciders in `D:/hof-acc9-work/coverage_check.py` and scored the committed
  `battery.json` myself.
* I wrote my own transcription of the repository's key-shape rule (`keyscan_mine.py`) and scanned
  every file the batch commit touched, with a positive control.
* I ran the gate, `--list`, `--list --ignored` and `fmt --check` in my own build directory
  (`D:/hof-acc9-target`, 9.1 G), after checking free space first and confirming no `cargo`/`rustc`/
  `hoh` process before or after.
* I cloned the repository to `D:/hof-acc9-clone` (316 tracked files, **no `runs/`**) and ran the
  three evidence test binaries there in `D:/hof-acc9-clone-target` — the decisive test of "does the
  repository alone suffice".

## 2. Per-headline reproduction, from committed files alone

`R` = reproduced in the working tree from committed files only; `clone` = what a fresh clone gives.

| headline | index value | mine (working tree) | clone | verdict |
|---|---|---|---|---|
| `cost.trajectories_total_bytes` | 4,166,273 | 4,166,273 | **4,197,568** | reproduced here, **not in a clone** |
| `cost.live.total_tokens` | 3,651,120 | 3,651,120 (150 calls; 3,537,843 + 113,277) | same | R |
| `cost.live.ratio_to_target` | 2.4341 | 2.4341 | same | R |
| `cost.round4.iter1.total_tokens` | 2,626,195 | 2,626,195 (69 calls) | same | R |
| `cost.round4.iter2.total_tokens` | 13,091,431 | 13,091,431 (125 calls) | same | R |
| `cost.round4.iter3.total_tokens` | 5,223,211 | 5,223,211 (102 calls) | same | R |
| `accounting.live.write_profile` | directive [6,14,17,19,43]; project [6,14,17,19,43,44,95]; failed [(139, src\game.rs, 1)]; window [95,151,55] | identical | same | R |
| `accounting.iter3.write_profile` | directive [6,50,70,73,74,80,84,86,90,93,97]; project [6,8,75,81,85,87,91,94,98]; failed [(22,…),(69,…)]; undecided [72]; window [8,75,66] | identical | same | R |
| `accounting.withdrawn_k32.live` | 76 / 1,357,530 / dir [] / proj [95] | identical | same | R |
| `accounting.withdrawn_k32.iter3` | 39 / 1,604,038 / ten directives / seven project | identical | same | R |
| `accounting.bands` | 37 / 43 / 52 / 51 | identical | same | R |
| `coverage.registry` | 19 ids | 19 anchors each present in the frozen PRD | same | R |
| `coverage.recorded_round4` | 13 / 2 / 4 of 19 (gaps Q-startup, B2.1) | identical | same | R |
| `coverage.with_the_new_step` | 15 / 0 / 4 of 19 | identical as a **code projection** | same | R (projection, not an observation — E-2) |
| `observation.round4.battery_steps` | 11 records, 9 E3, all ok | identical | same | R |
| `observation.round4.raw_calls` | 57 files | 57; but 2–3 sub-requests each (E-5) | same | R with the wording defect |
| `observation.round4.tester_claims` | 6/8 each iteration | identical, gap ids differ per iteration | same | R |
| `gate.counts_at_the_start_tree` | 782 / 0 / 6 / 788 | the named command gives **806** | 806 | **not reproducible** (E-6) |

Also reproduced from the committed files alone: the four per-file byte sizes (1,041,144 / 602,673 /
1,786,110 / 736,346), the iter-1 and iter-2 profiles the previous acceptance published
(iter-1 both signals `[7,8,9,13,14,18]`; iter-2 directives and project lists and the failed call 68),
the K=32 round-4-iter-1 abort (51 / 1,790,635) and iter-2 never firing, the 43-call and 66-call
windows, and the round's identity fields (below).

**The claim about what remains unreproducible** is substantially right — the provider's usage outside
the four committed trajectories, byte-level write identity, the withdrawn budget's live behaviour, the
other five round-4 attempts' `.hoh` evidence and the corpus's faithfulness to `runs/**` are all
outside the repository — but the list is not exhaustive (R-4) and, more importantly, it omits the one
thing that actually breaks: **the byte-exact corpus itself**, which a checkout rewrites.

## 3. The reproducibility defect, in full

`core.autocrlf` is `true` on this machine, from the **system** gitconfig, and the repository's own
`.gitattributes` says so. It pins `-text` for `.githooks/**`, `scripts/*.sh` and
`.spec/bevy/PRD.md` — the last because a fresh checkout had already broken the PRD's sealed prefix
once. Nothing pins `evidence/**`. The copier wrote LF bytes into the working tree; a checkout turns
every one of them into CRLF:

| file | working tree | clone | delta | CRLF in orig / clone |
|---|---|---|---|---|
| `evidence/cost/livecost1-iter-1…json` | 1,041,144 | 1,052,155 | +11,011 | 0 / 11,011 |
| `evidence/cost/round4-iter-1…json` | 602,673 | 607,159 | +4,486 | 0 / 4,486 |
| `evidence/cost/round4-iter-2…json` | 1,786,110 | 1,794,665 | +8,555 | 0 / 8,555 |
| `evidence/cost/round4-iter-3…json` | 736,346 | 743,589 | +7,243 | 0 / 7,243 |
| `evidence/index.json` | 13,319 | 13,541 | +222 | 0 / 222 |
| `evidence/README.md` | 3,488 | 3,553 | +65 | 0 / 65 |
| `.spec/bevy/PRD.md` (pinned) | 7,819 | 7,819 | 0 | 0 / 0 |
| `DECISIONS.md` | 1,306,821 | 1,318,434 | +11,613 | 0 / 11,613 |

The delta is exactly one byte per newline, and the files are equal after removing CR, so the JSON
parses and the **numeric** analysis is unaffected: in the clone, `write_accounting` is **7/7 green**
and `prd_coverage` is **5/5 green**. What breaks is the byte-level pinning:

```text
evidence_reproduction: 5 passed; 2 failed
  the_committed_cost_corpus_is_the_recorded_one
    assertion `left == right` failed: the four trajectories' own bytes
      left: 4197568   right: 4166273      (tests/evidence_reproduction.rs:90)
  the_evidence_index_names_committed_files_and_commands
    assertion `left == right` failed: the index's byte count must be the corpus that is here
      left: Some(4771139)   right: Some(4827317)
```

A clone's `cargo test --offline` therefore exits non-zero. This is a **fail** for the criterion
"make the cost and observation conclusions reproducible from the repository": the repository alone
reproduces 16 of the 18 headlines and all of the analysis, but not the corpus bytes, and not a green
gate.

## 4. Decidability

* **The identifiers are the frozen document's own.** All 19 anchors are literals in
  `.spec/bevy/PRD.md`. `P1..P5` and `C1..C6` are the document's own labels, `B2.1..B2.4` its own
  appendix numbering. `Q-scale`, `Q-startup`, `Q-not-required`, `Q-perf` are harness-coined names,
  but each is anchored to the literal bolded title of one of the four §4 clauses — so the *set* is
  the document's structure and the *names* are stable pointers into it. They are not invented to fit
  what the harness can see: four of the nineteen (`C5`, `C6`, `Q-scale`, `Q-not-required`) are
  `Unobservable` and are in the denominator precisely because the document has them.
* **The figure is comparable between rounds.** The denominator is a compile-time constant checked
  against `EXPECTED_IDS`, and `decide()` reads only `(step_id, ok)` pairs; the Tester's claims cannot
  move it, and a test builds round-3-shaped and round-4-shaped bundles and shows both carry 19. A
  step that never ran is a `Gap` naming it, never a pass — the RA-5 false-green shape is pinned.
* **The two previously open gaps.** `P3-goal-x` is named as outside the frozen contract, with the
  reason published in `RESIDUALS` and in the report; it is kept out of the denominator because it is
  not a PRD surface. `S1-deterministic-step` has a real decider (`e3_process_liveness`, last step,
  `bevy_wait_frames(1)` then `(8)`, delta ≥ 8, persisted to `.hoh/deterministic/raw/`) that reuses
  the frozen `FrameCounter` surface and the existing tool — but it has **never been observed**: no
  `raw/e3_process_liveness.json` exists and the batch's own `unverified` concedes the live path has
  never run. It is closed *in code*, not *by an observation* (E-2). That is the one place where the
  batch's headline disposition outruns its evidence.
* **The frozen documents were kept intact.** `git diff 5f526d2 201af0a` touches only the two
  reports authorised for the D-1 correction, the new report, `DECISIONS.md` (append-only) and the
  code/evidence the batch added. `PRD.md`, `REQUIREMENTS.md`, `DESIGN-OVERVIEW.md`,
  `DESIGN-DETAIL.md`, both acceptances, `ROUND-4-REPORT-COMPLETE.md`, `COST-REPORT.md`,
  `FIX-REPORT.md`, both spike reports and `config/hoh.yaml` are byte-identical across the commit.

## 5. D-1 restated, reproduced

| K | what my replay does to the live call | what it does to round-4 iter-3 |
|---|---|---|
| 32 | aborts at 76, 1,357,530, project write 95 still after it | aborts at 39, 1,604,038, cuts 10 directives and 7 project edits |
| 37 | aborts at 81, 1,484,934 — the last abort under the 1,500,000 target | — |
| 38 | aborts at 82, 1,511,382 — over target | — |
| 42 | — | aborts at 49 and cuts `75..98` |
| 43 | aborts at 87 with `project_writes_after = [95]` — the write the old text called safe is refused | **never fires** |
| 50 | aborts at 94, cuts the call-95 write | — |
| 51 | aborts at 95; the write never happens (empty after-list) | — |
| 52 | aborts at 96; nothing recorded is cut | — |

So the corrected floor is **K ≥ 52** (K ≥ 51 under the replay's strict `> abort` convention), and
**37 < 43 < 52**: the bands do not overlap and the losing side is worse than the round-6 report said.
The restatement is present in both reports' machine blocks and prose, quotes the old `K ≥ 43` wording
instead of erasing it, is in `DECISIONS.md` D305, and is pinned by tests that exist.

## 6. The gate, on the working tree

* Free space first: D: 252 G, F: 57 G. Nothing needed deleting; I deleted nothing. My own build
  artefacts, measured: `D:/hof-acc9-target` **9.1 G**, `D:/hof-acc9-clone-target` **1.7 G**,
  `D:/hof-acc9-clone` 87 M, `D:/hof-acc9-work` 2.8 M.
* `cargo test --offline` → **literal exit code 0**: **800 passed / 0 failed / 6 ignored / 806
  listed** over 60 `test result:` lines, in `D:/hof-acc9-target`.
* `cargo test --offline -- --list` → exit 0, 806 names; `-- --list --ignored` → exit 0, six names,
  the same six the report lists, every one present in the full list.
* `cargo fmt --all --check` → exit 0, **0 bytes** on stdout and stderr.
* **0** `warning:` lines; the only lines containing "warning" are five test names.
* **No test removed**: the commit adds 18 `#[test]`/`#[tokio::test]` attributes and removes 0; the
  intervening `05604b9`→`5f526d2` commit is docs-only, so the 788 baseline holds and 788 + 18 = 806.
* No `cargo`/`rustc`/`hoh` process before or after.

The clone's gate is the separate, failing case in §3.

## 7. Key material, and the honesty of the tools

No key-shaped material in anything added. My own transcription of
`src/runtime/secrets.rs`'s rule, plus a broader vendor regex, over all **139** files the commit
touched: no repo-rule finding; the only broad-regex hit is the literal `sk-late-occurrence` inside
`keyscan.py`'s own allowlist, an 18-character placeholder that is below the shape test's 16-character
body threshold. A synthetic positive control **does** fire, so the scanner is not written so it
cannot find anything.

`evidence/tools/keyscan.py` is honest: it transcribes the prefix/body and assignment/value rules
exactly, its `ALLOWED` list is byte-identical to `tests/credential_scan.rs::ALLOWED_PLACEHOLDERS`
(whose two entries are below the thresholds, so the allowlist weakens nothing), it reports
fingerprints and lengths rather than values, and `build_evidence.py` refuses a key-shaped file
**before** copying it. The repository's own scan covers `evidence/` (it excludes only `.git`,
`target`, `.workspace`, `runs`, `node_modules`), so the report's "recomputed by
`credential_scan`" is a real check.

## 8. Tree coherence

* 316 tracked files; the top level is the harness plus this engine's flow and `evidence/` only;
  `git ls-files runs` is empty.
* `DECISIONS.md` is append-only across the commit: 1,295,073 → 1,306,821 bytes, the old bytes a byte
  prefix of the new file, +11,748 appended (D305).
* The round-4 launch ledger holds **7** launches with 7 distinct nonces, pids and launch images; its
  last line (nonce `faf2adda-c698-48ef-a4f5-f51d1da551c6`, pid 47624, port 15702,
  `http://127.0.0.1:15702/`) is exactly the launch `meta.json` and `launch.json` publish as
  `verified: true`, and the identity rule is stated as the per-launch nonce read back from
  `hof_game::contract::ProcessNonce`.
* Identity, tripwire, fold and resume behaviour are inside the green gate.
* `git status --porcelain` is empty at HEAD `201af0a`; HEAD is **not** `origin/bevy-core` (which is
  `5f526d2`), so nothing has been pushed — by the batch or by me.

## 9. Counterexamples I looked for

* **A headline a clone cannot reproduce.** Found: `cost.trajectories_total_bytes`, and it takes the
  index's own test down with it (E-1). I looked for this because the batch's claim was specifically
  about a clone.
* **A key scanner that cannot fail.** Not found: the positive control fires and the allowlist is
  inert.
* **An anchor that is not in the frozen document.** Not found: all 19 are present; one
  (`Q-not-required` → `**不要求**`) occurs twice, which is harmless for a `contains` check but means
  the anchor is not a unique pointer.
* **A decider that reads the Tester.** Not found: `decide()` takes only step outcomes, and a
  never-recorded step is a named gap.
* **A restatement that moved the wrong bound.** Not found: my replay independently gives 52/51 and
  43, and 37 for the pass edge.
* **A removed test.** Not found: 18 added, 0 removed.
* **A surface-count that contradicts the frozen document.** Found: "eight" where the PRD says seven
  (E-3).
* **An index number with no reproducible source.** Found: `gate.counts_at_the_start_tree` (E-6) and
  the raw-call wording (E-5).

## 10. What I could not establish

I did not read or measure the gitignored `runs/**` tree, by instruction, so I cannot confirm that the
committed corpus is a faithful subset of it — nor the claim that `runs/**` is 11,229 files /
12,775,066,006 bytes / 11.898 GiB. I ran only the Windows clone, so I cannot *demonstrate* that a
Linux or macOS clone (where `core.autocrlf` is false by default) passes; the mechanism says the blobs
are LF and it would, but I did not run it. I did not re-derive the lever pairs or the
`compact_history` projections. I cannot decide byte-level identity of what a successful shell write
put on disk, and neither can the recording.

## 11. What stands between this tree and the goal's five criteria

1. **Decidability** — now satisfied. The denominator is the frozen PRD's own 19 surfaces, it cannot
   move with the Tester, every item carries its evidence or a named reason, and two rounds compare
   directly. One caveat to carry: the `S1` closure is code-level, not observed.
2. **Reproducibility / evidence** — **not satisfied**, because of E-1. The evidence now exists in the
   repository and the analysis reproduces from it, but the repository does not carry its own corpus
   byte-for-byte and its own added tests go red on a clean checkout on this machine. One
   `.gitattributes` line (`evidence/** -text`) plus a re-run of the clone check closes it.
3. **The cost criterion** — still unmet, as expected: **2.434×** the 1,500,000 target on the one live
   Developer call, and the D-1 restatement makes the withdrawn lever's damage larger, not smaller.
   Nothing in this batch changes that.
4. **The honest-acceptance criterion** — met: the two reports were corrected only where factually
   wrong, quoted the old wording, and are pinned by tests.
5. **The frozen-contract criterion** — met: the frozen documents and the seal are untouched, and the
   PRD's own append-only rule is respected.

**Verdict: `fail`.** Two of the six verifications fail or carry a medium defect (E-1 is high and
blocks; E-2 is medium), while four pass. The failure is narrow, precise and one line to fix, but a
`pass` here would authorise a push of a tree whose own suite is red on a fresh clone — which is the
opposite of what the batch was for.
