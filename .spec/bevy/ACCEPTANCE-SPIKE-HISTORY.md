```json
{
 "verdict": "fail",
 "reviewed_artefact": ".spec/bevy/SPIKE-HISTORY-WINDOW.md",
 "reviewer": "independent acceptance subagent (no prior context)",
 "date": "2026-10-06",
 "headline": "The central finding SURVIVES: in round4-iter-2 the Developer read src/game.rs whole at call 5 and rewrote it at call 33 with no other read in between (28 steps against a passing window of at most 4), and 129 substantive lines of the call-33 write body occur nowhere else in the recorded context between the read and the write and are absent from the N=4 window. The STEP policy table, its boundary and the token/byte calibration reproduce to the token. The BYTE policy table does NOT: the claimed max_bytes_passing_all_four=49152 is wrong by 3.6x-5.8x (true value 13543 exclusive or 8443 inclusive) because the spike's byte-window accumulator over-counts and closes early. The numbers are therefore NOT all safe as the basis for a decision, although the error strengthens rather than weakens the report's conclusion.",
 "criteria": [
  {
   "id": "C1-reconstruction",
   "pass": true,
   "evidence": "Rebuilt all 4 recordings independently. calls 69/125/102/150 and sent wire bytes 9896402/50007767/19753905/10937231 match the report exactly; each call count equals the trajectory's own hoh.usage.calls and each summed prompt/completion/total equals its hoh.usage. system prompt 14490 chars / 14849 wire bytes, task 1279 / 1365, first call 16214 B -> 4269 tokens. System prompt identical across the four except the iteration digit. Largest single messages match (idx21 tool 42467 B, idx150 assistant 32443 B, idx140 assistant 32175 B in iter-2; idx17 assistant 45807 B, idx10 tool 34689 B in iter-3; idx314 tool 10341 B, idx319 tool 8227 B in live). 50007767 equals COST-REPORT.md tail_curve_wire_bytes_iter_2.sent (line 51) and 20447131 equals its measured_developer_prompt_before (line 66), so the reconstruction reproduces the repository's own published prompt totals. Undocumented nuance: 38 of 296 round-4 calls are user-role format-error retries carrying the failed response's usage (iter-1 20, iter-2 10, iter-3 8); this does not break the reconstruction."
  },
  {
   "id": "C2-token-per-byte",
   "pass": true,
   "evidence": "pooled 20447131/79658074 = 0.2566862 (report 0.256686); pooled OLS slope 0.254403, intercept 614.36, worst residual 1159.3 (report 0.254403/614.36/1159); iter-2 alone 0.255366/-38.28/1347.3 (report 0.255366/-38.28/1347); per-recording ratios 0.257120/0.255270/0.260054; live 0.323468. Caveat: the live fit is poor (slope 0.2171, intercept 7757.7, worst residual 7008 tokens, per-call ratio 0.2518-0.7062), and 'the iter-2 fitted total equals the iter-2 recorded total' is an identity of OLS with an intercept, not corroboration."
  },
  {
   "id": "C3-projection-steps-and-boundary",
   "pass": true,
   "evidence": "Step policy reproduces to +/-2 tokens. N=4 total_with_completion = 539101 / 1474826 / 752075 / 1077207 (report 539102 / 1474827 / 752076 / 1077207); N=5 iter-2 = 1631524 (report 1631526). Boundary confirmed: binding trajectory round4-iter-2, largest passing window N=4, next larger N=5 fails on iter-2 alone; sensitivity boundary N=2 also confirmed. Margin at N=4 is only 25174 tokens (1.68%), i.e. about 2.7 extra calls."
  },
  {
   "id": "C4-projection-bytes-and-boundary",
   "pass": false,
   "evidence": "REFUTED. The stated policy ('keep the last B wire bytes of steps') passes all four at most at B=13543 (exclusive; live 1499796, fails at 13544 with 1500020) or B=8443 (inclusive; iter-2 1499038, fails at 8444 with 1500170), not 49152. Under the sensitivity ratio the edges are 13543 and 2782, not 32768. Cause found: F:/spike-history-window/final.py::window_bytes accumulates step=sum(b[pos[j-1]:bi]) (a cumulative slice) into an already-inflated 'used', so the loop breaks early and the kept window is smaller than the policy names; a verbatim port reproduces the report's whole byte table, while the stated policy does not reproduce it."
  },
  {
   "id": "C5-decisive-claim",
   "pass": true,
   "evidence": "Verified from raw messages. call 5 (msg idx13) = 'type src\\game.rs', observation 14902 chars = the whole file. calls 6..32 contain no other read; only the 'echo HOH_WRITE_FILE src/game.rs' probe at call 13. call 33 (idx72) = full HOH_WRITE_FILE src/game.rs (21246 byte body). gap = 28 steps. Content test: of 383 substantive write-body lines, 142 occur verbatim in the call-5 read; 129 of those occur nowhere else in the recorded text of calls 6..32, and 0 of the 129 are inside the N=4 window (calls 29..32). Where a small window did suffice: at N=4 iter-3 drops 0/9 edges and live has no edges; the negative result is carried by iter-1 (1/6) and iter-2 (4/11). At the corrected byte edge (B=12288) iter-2 drops 11/11, iter-1 4/6, iter-3 2/9 - stronger than the report claims."
  },
  {
   "id": "C6-edge-counts-per-window",
   "pass": true,
   "evidence": "Independent re-implementation reproduces every reported count: iter-1 6 edges gaps 5,4,4,2; iter-2 23 write events / 11 edges gaps 28,10,5,5,4; iter-3 19 / 9 gaps 4,4,3,3,2; live 1 / 0. Gaps and the decisive case match exactly. Defect in the label: successful_project_write_events is not project-only (iter-2 23 total = 11 project + 12 scratch; iter-3 19 = 9 + 10; live 1 = 0 + 1). The byte dropped-edge rows (B16384, B32768) inherit the D1 over-count and are too generous."
  },
  {
   "id": "C7-alternative-explanations-and-open-levers",
   "pass": true,
   "evidence": "The report discloses that a windowed role would re-read and that the replay cannot price it. I priced the headroom instead: 1.68% at N=4 and 3.67% at the corrected byte edge, so ~3 and ~6 extra calls exhaust the band - the conclusion is robust to, and strengthened by, the re-read hypothesis. Levers the spike does not consider (scope, not defect): cap or summarise tool observations and whole-file write arguments, which are re-sent on every later call; keep a working set of files in play (recommended in the report's section 7 but not measured); prompt caching (cache_hit_tokens is null in all four recordings); and shrinking the per-invocation call count, which dominates the cost term."
  },
  {
   "id": "C8-gate",
   "pass": true,
   "evidence": "Own build dir F:/acc-hw-target, sequential, no rm -rf and no wildcards, free disk checked before (27899 MB) and after (18597 MB). cargo test --offline exit code 0 with 800 passed / 0 failed / 6 ignored / 806 listed, 60 test result lines, 0 warning lines; cargo test --offline -- --list exit 0 with 806 names; --list --ignored exit 0 with 6; cargo fmt --all --check exit 0 with 0 bytes of output. Identical to the stated baseline 800/0/6/806, so no test was removed; 806 = 800 + 6. git status --porcelain empty before the gate; HEAD 8f06ce69b75496736ae7e410a27d051ac5e34c37. The named flaky test adapter::bevy::brp::tests::a_slow_reply_that_exceeds_the_timeout_is_a_timeout is listed, not ignored, and passed."
  },
  {
   "id": "C9-first-run-flake-disclosure",
   "pass": false,
   "evidence": "Cannot be confirmed. F:/spike-history-window/gate.out is the clean re-run (60 test result lines, 800 passed) and no log of the exit-101 run survives anywhere in the tree, so the disclosed failure (440 passed / 1 failed / 0 ignored / 441 listed on the named timeout test) is honest and plausible but unverifiable by me. The clean-run gate verdict is unaffected."
  }
 ],
 "recomputed_numbers": {
  "sent_wire_bytes": {
   "round4-iter-1": 9896402,
   "round4-iter-2": 50007767,
   "round4-iter-3": 19753905,
   "livecost1-iter-1": 10937231
  },
  "recorded_prompt_tokens": {
   "round4-iter-1": 2544563,
   "round4-iter-2": 12765478,
   "round4-iter-3": 5137090,
   "livecost1-iter-1": 3537843
  },
  "pooled_ratio_of_totals": 0.2566862337,
  "pooled_ols_slope": 0.254403,
  "pooled_ols_intercept": 614.36,
  "pooled_ols_worst_residual": 1159.3,
  "iter2_ols_slope": 0.255366,
  "iter2_ols_intercept": -38.28,
  "iter2_ols_worst_residual": 1347.3,
  "steps_N4_total_with_completion": {
   "round4-iter-1": 539101,
   "round4-iter-2": 1474826,
   "round4-iter-3": 752075,
   "livecost1-iter-1": 1077207
  },
  "steps_N5_total_with_completion": {
   "round4-iter-1": 581360,
   "round4-iter-2": 1631524,
   "round4-iter-3": 811875,
   "livecost1-iter-1": 1114159
  },
  "max_passing_bytes_exclusive": 13543,
  "max_passing_bytes_inclusive": 8443,
  "max_passing_bytes_exclusive_sensitivity": 13543,
  "max_passing_bytes_inclusive_sensitivity": 2782,
  "max_passing_steps": 4,
  "max_passing_steps_sensitivity": 2,
  "decisive_case": {
   "read_call": 5,
   "write_call": 33,
   "gap_steps": 28,
   "write_body_bytes": 21246,
   "read_observation_chars": 14902,
   "substantive_write_lines": 383,
   "lines_shared_with_read": 142,
   "lines_unique_to_read": 129,
   "lines_unique_to_read_in_N4_window": 0
  },
  "edge_counts": {
   "round4-iter-1": {
    "write_events_all": 6,
    "project_only": 6,
    "edges": 6
   },
   "round4-iter-2": {
    "write_events_all": 23,
    "project_only": 11,
    "edges": 11
   },
   "round4-iter-3": {
    "write_events_all": 19,
    "project_only": 9,
    "edges": 9
   },
   "livecost1-iter-1": {
    "write_events_all": 1,
    "project_only": 0,
    "edges": 0
   }
  },
  "gate": {
   "exit_code": 0,
   "passed": 800,
   "failed": 0,
   "ignored": 6,
   "listed": 806,
   "test_result_lines": 60,
   "warning_lines": 0,
   "fmt_exit_code": 0,
   "fmt_output_bytes": 0,
   "list_exit_code": 0,
   "list_count": 806,
   "list_ignored_exit_code": 0,
   "list_ignored_count": 6,
   "head": "8f06ce69b75496736ae7e410a27d051ac5e34c37"
  }
 },
 "defects": [
  {
   "id": "D1",
   "severity": "high",
   "what": "The byte-policy table, passing_band.max_bytes_passing_all_four (claimed 49152) and the byte side of the sensitivity band (claimed 32768) are wrong by 3.6x-5.8x. A faithful implementation of the stated 'last B wire bytes of steps' policy passes all four at most at B=13543 (exclusive) or B=8443 (inclusive). Cause: final.py::window_bytes accumulates a cumulative slice (step=sum(b[pos[j-1]:bi])) into an already-inflated 'used', breaking the loop early; every byte row is optimistic.",
   "reproduction": "python F:/acc-hw/verify2.py (verbatim port reproduces the report's byte table); python F:/acc-hw/deps_verify.py and python F:/acc-hw/bands.py (stated policy: 13543 / 8443, exact edges by binary search)."
  },
  {
   "id": "D2",
   "severity": "medium",
   "what": "successful_project_write_events is not project-only: the detector counts every write event including .hoh/scratch/** script and note writes before filtering to project paths for the edges. Reported iter-2 23 = 11 project + 12 scratch; iter-3 19 = 9 + 10; live 1 = 0 + 1; only iter-1 (6) is all-project. The prose overstates project writes by up to 2x.",
   "reproduction": "python F:/acc-hw/deps_verify.py prints write_events(all) beside project_only."
  },
  {
   "id": "D3",
   "severity": "low",
   "what": "The live rows rest on a bytes->tokens relation that does not hold (slope 0.2171, intercept 7757.7, worst residual 7008 tokens, per-call ratio 0.2518-0.7062) yet are presented under a single 0.323468 calibration; the corrected byte band edge is decided by exactly these rows.",
   "reproduction": "python F:/acc-hw/fit.py; python F:/acc-hw/extras.py"
  },
  {
   "id": "D4",
   "severity": "low",
   "what": "'iter_2_fit_total equals iter_2_recorded_total' is offered as support but is an identity of OLS with an intercept (residuals sum to zero), so it corroborates nothing.",
   "reproduction": "python F:/acc-hw/fit.py"
  },
  {
   "id": "D5",
   "severity": "low",
   "what": "The method note omits that 38 of the 296 round-4 model calls are user-role format-error retries carrying the failed response's usage (iter-1 20, iter-2 10, iter-3 8). The reconstruction remains correct but this is not visible to a reader.",
   "reproduction": "python F:/acc-hw/retries.py"
  }
 ],
 "risks": [
  "The decision is still available and points the same way: the correct pair of band edges is 4 steps and ~13.5 KiB (or ~8.4 KiB), both far short of the recorded 28-step dependency, so the non-overlap argument holds on either number and the correction makes it stronger.",
  "The passing band is definition-sensitive and nearly marginless: N=4 passes iter-2 by 1.68% and the current-step-counting variant (N=5) overruns by 1.09x; the byte window spans 13543 vs 8443 between its two readings. No policy should be called 'passing' without stating the grain.",
  "No live confirmation exists for any passing row, and every row is arithmetic over call sequences the window would itself have changed; with 1.68% headroom the projection is an upper bound on the policy's attractiveness.",
  "The live recording, the least interpretable of the four (fold notes; unusable content analysis), is the binding recording for the corrected byte band."
 ],
 "unverified": [
  "The report's first, failing gate run (exit 101; 440 passed / 1 failed / 0 ignored / 441 listed on adapter::bevy::brp::tests::a_slow_reply_that_exceeds_the_timeout_is_a_timeout): no log survives, only the clean re-run's output.",
  "Any live windowed run or any live confirmation of the projection; none exists offline.",
  "How a windowed role would actually behave (re-reads and call count); argued, not measured.",
  "The complete script-mediated project-write population for iter-2 and iter-3; I reproduced the spike's counts and gaps but did not reconstruct every scripted write independently."
 ],
 "central_finding_survives": true,
 "numbers_safe_as_decision_basis": false
}
```

# ACCEPTANCE — `SPIKE-HISTORY-WINDOW.md` (bounded-history window, offline replay)

**Reviewer:** independent acceptance subagent. No prior context; every number below was re-derived from
`evidence/cost/*.developer.attempt1.json` or from a fresh gate run, not taken from the artefact.
**Date of review:** 2026-10-06. **Reviewer's build dir:** `F:/acc-hw-target` (own; the repo's `target/` was
not used). **Reviewer's scripts:** `F:/acc-hw/` (outside the repository). **Nothing was committed, staged
or pushed; no file under `src/**`, `tests/**`, `evidence/**`, `runs/**`, `config/**` or any frozen document
was touched; the only file added to the repository is this one.**

## Bottom line

**The central finding survives, and I could not break it.** The report's decisive measurement — that in
`round4-iter-2` the Developer read `src/game.rs` whole at call 5 and rewrote it at call 33 with no other
read in between, a 28-step gap against a passing window of at most 4 steps — is exactly what the raw calls
contain, and I strengthened it from content (129 substantive lines of the call-33 write body occur nowhere
else in the recorded context between the read and the write, and none of them are inside the N=4 window).
The *step* policy's whole table and its boundary reproduce to the token.

**Its numbers are not all safe to use as the basis for a decision.** The **entire byte-policy table** (16
policies × 4 recordings), the `max_bytes_passing_all_four` figure and the byte side of the sensitivity
band are **wrong by a factor of 3.6×–5.8×**, because the spike's byte-window accumulator over-counts and
closes the window early. The report's byte side is the *only* place where its two headline band edges
(`4 steps` / `49,152 bytes`) can be compared, and one of the two is not what it says.

The error runs in a direction that **strengthens** the report's conclusion: a correctly implemented byte
window is more expensive, so the true passing byte window is ~8.4–13.5 KiB, not 49,152 B, and a smaller
window discards *more* of the content the role used (at B = 12,288, `round4-iter-2` loses 11 of its 11
recorded read/write→write edges, not 6). The verdict below is therefore `fail` **on the artefact's
numbers**, not on its conclusion: the conclusion stands, the evidence table must be corrected before a
human uses it.

---

## 1. The reconstruction — **CONFIRMED**

I rebuilt every call from the recordings: the wire size of each message is
`json{role, content, tool_calls, tool_call_id}` serialised compactly with the local `extra` block excluded,
and model call *k* is located at the message carrying `extra.response.usage`, whose prompt is
`messages[0:k]` (system + task + steps 1..k-1).

| recording | calls | sent wire B (mine) | report | recorded prompt (mine) | report | completion | total | ratio (mine) | report |
|---|---|---|---|---|---|---|---|---|---|
| round4-iter-1 | 69 | 9,896,402 | 9,896,402 | 2,544,563 | 2,544,563 | 81,632 | 2,626,195 | 0.257120 | 0.257120 |
| round4-iter-2 | 125 | 50,007,767 | 50,007,767 | 12,765,478 | 12,765,478 | 325,953 | 13,091,431 | 0.255270 | 0.255270 |
| round4-iter-3 | 102 | 19,753,905 | 19,753,905 | 5,137,090 | 5,137,090 | 86,121 | 5,223,211 | 0.260054 | 0.260054 |
| livecost1-iter-1 | 150 | 10,937,231 | 10,937,231 | 3,537,843 | 3,537,843 | 113,277 | 3,651,120 | 0.323468 | 0.323468 |

* Every call count equals the trajectory's own `hoh.usage.calls`, and every summed prompt/completion/total
  equals the trajectory's own `hoh.usage` — so the call set is the harness's own call set, not my choice.
* System prompt **14,490 chars / 14,849 wire bytes**; task **1,279 chars / 1,365 wire bytes**; first call
  **16,214 B → 4,269 recorded prompt tokens** — all three confirmed. The system prompt is byte-identical
  across the four except the literal iteration digit (`1`→`2`, `1`→`3`); `livecost1-iter-1` is iteration 1
  and is identical to `round4-iter-1`.
* Largest single messages, checked individually: iter-2 tool idx21 **42,467 B**, assistant idx150
  **32,443 B**, assistant idx140 **32,175 B**; iter-3 assistant idx17 **45,807 B**, tool idx10
  **34,689 B**; live tool idx314 **10,341 B**, tool idx319 **8,227 B**. All as reported.
* **Does it reproduce the repository's own published totals?** Yes. `50,007,767` is
  `COST-REPORT.md`'s `tail_curve_wire_bytes_iter_2.sent` (line 51); `20,447,131` is its
  `measured_developer_prompt_before` (line 66); `0.323468` is `LIVE-COST-REPORT.md`'s
  `live_measured_tokens_per_wire_byte` (line 131) and is recomputed identically here.
* One thing the report's method note does not say, which I had to discover and then satisfy myself is
  harmless: **38 of the 296 round-4 "model calls" are not assistant messages.** They are the user-role
  format-error retries (`"No tool calls found in the response..."`) and each carries the failed response's
  own `usage` — iter-1 has 20, iter-2 10, iter-3 8, live 0. Counting them as their own steps is consistent
  (the prompt at such a message is still `messages[0:k]`, and the harness counts them as calls), so the
  reconstruction is correct; it is simply an undocumented property of the corpus a reader should know.

## 2. The token-per-byte figure — **CONFIRMED**

| quantity | mine | report |
|---|---|---|
| pooled ratio of totals, 296 round-4 calls | 20,447,131 / 79,658,074 = **0.2566862** | 0.256686 |
| pooled least-squares slope / intercept / worst residual | **0.254403 / 614.36 / 1,159.3** | 0.254403 / 614.36 / 1159 |
| iter-2 alone: slope / intercept / worst residual | **0.255366 / −38.28 / 1,347.3** | 0.255366 / −38.28 / 1347 |
| per-recording ratio of totals | 0.257120 / 0.255270 / 0.260054 | same |
| live (folded) ratio of totals | **0.323468** | 0.323468 |

I confirm the numbers. Two observations about their standing:

* `iter_2_fit_total == iter_2_recorded_total` (COST-REPORT lines 44–45, repeated implicitly as support) is
  an algebraic tautology of an OLS fit *with an intercept*: residuals sum to zero, so the fitted total
  equals the recorded total for any data. It corroborates nothing.
* The live ratio is a ratio of totals over a genuinely **bad** fit: for `livecost1-iter-1` the least-squares
  slope is 0.2171 with intercept 7,757.7 and a worst single-call residual of **7,008 tokens** (rms 2,261);
  the per-call ratio ranges from **0.2518 to 0.7062** (p90 = 0.5065). Every live row therefore carries
  model error of thousands of tokens. This matters because the live recording is the recording that binds
  the corrected byte window (below). The report's claim that 0.323468 is an upper bound is true for the
  *unfolded* rows (their per-call ratios span 0.2494–0.2699), and it is the correct scale for a *total* of
  the live rows, but it is not an upper bound per live call.

## 3. The projection — **steps CONFIRMED, bytes REFUTED**

The replay holds the recorded call sequence fixed (69 / 125 / 102 / 150 calls) and changes only prompt
size. That assumption is disclosed by the report and is the projection's main weakness; see §5 for its
price.

**Steps (`keep_last_N_steps`), total_with_completion, mine vs report:**

| N | r4-i1 | r4-i2 | r4-i3 | live | report r4-i2 |
|---|---|---|---|---|---|
| 1 | 411,639 | 1,003,503 | 571,376 | 946,649 | 1,003,504 (total_with_completion) |
| 2 | 454,166 | 1,160,650 | 631,917 | 993,111 | 1,160,651 |
| **4** | 539,101 | **1,474,826** | 752,075 | 1,077,207 | **1,474,827** |
| 5 | 581,360 | **1,631,524** | 811,875 | 1,114,159 | **1,631,526** |

The boundary is exactly where the report says it is: the binding trajectory is **`round4-iter-2`**, the
largest window passing all four is **N = 4**, and the next larger one (N = 5) fails on iter-2 alone.
Under the sensitivity ratio the boundary is also where the report says (N = 2 passes, N = 3 fails on
iter-2). The whole step table reproduces to ±2 tokens.

*(Method note, for the record: my first pass reconstructed an apparent `(N+1) × system-prompt`
under-count in the report's step rows. It was **my** bug — I added the retained `system + task` twice for
the calls whose window reaches the start of history. I found it by reading the spike's own surviving
helper script `F:/spike-history-window/final.py`, ported it verbatim, and reproduced the report's step
table, including the boundary. The step side of the report is exactly right; my earlier discrepancy was an
artefact of my own code, and I am stating that rather than hiding it.)*

**Bytes (`keep_last_B_wire_bytes`) — not reproducible as stated.** The report claims
`max_bytes_passing_all_four = 49,152`. The stated policy is "whole steps counted backwards from the newest
until B is reached". I implemented that two ways, and neither matches:

| reading of the stated policy | largest B passing all four | binding recording | report |
|---|---|---|---|
| exclusive — largest whole-step suffix whose byte total ≤ B | **13,543** (live 1,499,796; fails at 13,544 with 1,500,020) | livecost1-iter-1 | 49,152 |
| inclusive — keep adding until the total reaches B | **8,443** (iter-2 1,499,038; fails at 8,444 with 1,500,170) | round4-iter-2 | 49,152 |
| exclusive, sensitivity ratio 0.323468 everywhere | **13,543** | livecost1-iter-1 | 32,768 |
| inclusive, sensitivity ratio 0.323468 everywhere | **2,782** | round4-iter-2 | 32,768 |

The cause is now known exactly, because the spike's helper scripts survive at
`F:/spike-history-window/final.py`. Its `window_bytes` computes, for each candidate older step,
`step = sum(b[pos[j-1] : bi])` — a **cumulative** slice from that step to the current call — and tests
`used + step > param` against a `used` that has already been inflated by the previous cumulative slice. The
accumulator therefore grows faster than the window does, the loop `break`s early, and the window actually
kept is smaller than "the last B bytes" implies. For the newest step the guard `and j < k-1` forces
inclusion, which is why the smallest budgets still keep one step. The many byte rows I could not match with
*any* budget scaling of a correct implementation are all explained by this over-count.

Consequence: the report's byte table is systematically **optimistic** — every byte row is cheaper than the
policy it names — so the real passing band is smaller and more content is dropped. The report's own
`final.json` agrees with its printed table (`B49152` passes all four, `B65536` does not), so this is a
defect of the measurement, faithfully reported, not a transcription error.

**What the held-fixed assumption does to reliability.** The projection never lets the role react. At the
step band edge the margin is tiny: iter-2 projects to 1,474,826 against 1,500,000 — **25,174 tokens, 1.68 %**
— with a mean projected prompt of 9,191 tokens/call, so about **2.7 extra calls** exhaust it. At the
corrected byte edge the margin is 55,094 tokens on live (3.67 %) with a mean projected prompt of ~8,877 —
about **6 extra calls**. The report calls the projection "medium" confidence; on these numbers a windowed
role that re-reads *anything* it dropped blows the band almost immediately. The projection is an optimistic
bound with essentially no headroom, which is the opposite of reassuring for a policy that is claimed to pass.

## 4. The decisive claim — **CONFIRMED, and harder than the report states**

I verified the `round4-iter-2` case directly from the messages, not from the report:

* **call 5** (message idx 13) is `type src\game.rs`; its recorded observation is **14,902 characters** —
  the whole file. ✓
* **calls 6–32** contain no other read of `src/game.rs`: the only mention is the `echo HOH_WRITE_FILE
  src/game.rs` probe at **call 13** (72-byte observation). ✓
* **call 33** (message idx 72) is a full `HOH_WRITE_FILE src/game.rs` (21,246-byte body). ✓
* **gap = 28 steps.** ✓

I then tested the *substance* rather than the trace. The call-33 write body has 570 lines, 383 of them
substantive (≥ 12 non-space characters). 142 of those occur verbatim in the call-5 read. Of those 142,
only 13 occur anywhere else in the whole text of calls 6–32; **129 occur nowhere in the recorded context
between the read and the write except the call-5 read itself**, and **0 of those 129 are inside the N = 4
window (calls 29–32)**. The role reproduced a large block of file content it could only have had from a
step 28 back. The decisive case is real.

**Edge counts.** I re-implemented the dependency analysis from scratch and it reproduces the report's
counts exactly:

| recording | write events (all) | project-only | edges | largest gaps (mine = report) |
|---|---|---|---|---|
| round4-iter-1 | 6 | 6 | 6 | game.rs read@3→8 (5); contract.rs read@3→7 (4); game.rs write@14→18 (4); game.rs read@11→13 (2) |
| round4-iter-2 | 23 | **11** | 11 | game.rs read@5→33 (**28**); write@55→65 (10); write@37→42 (5); write@67→72 (5); read@51→55 (4) |
| round4-iter-3 | 19 | **9** | 9 | read@71→75 (4, `tweak3.ps1`); write@87→91 (4, `tweak7.ps1`); read@3→6 (3); write@91→94 (3, `tweak8.ps1`) |
| livecost1-iter-1 | 1 | **0** | 0 | — |

**Where a small window would in fact have sufficed.** At N = 4, `round4-iter-3` drops **0 of 9** edges
(its largest gap is exactly 4) and `livecost1-iter-1` has no edges at all. The negative result is carried
by iter-1 (1 dropped of 6) and iter-2 (4 of 11). At the *corrected* byte band edge (B = 13,543) the
picture is worse than the report paints: at B = 12,288, iter-2 already drops **11 of 11** edges, iter-1
drops 4 of 6, and iter-3 drops 2 of 9. So the report's headline — *a passing window is exactly a window
that discards content the role used* — survives; if anything the corrected numbers make it hold for more
recordings, not fewer. The report's own byte dropped-edge rows (`B16384`, `B32768`) inherit the over-count
bug and are too generous; correcting them only adds dropped edges.

## 5. Alternative explanations and unconsidered levers — **the conclusion is robust, but the report under-prices it**

The report itself notes the roles re-read files often and that a windowed role would "plausibly re-read…
which raises call count and cost in a way this replay cannot price". I priced the headroom instead, and the
answer is stark: the passing window passes by **1.68 %** on the binding trajectory. A windowed role needs
only ~3 extra calls to fail. Since the recorded Developer in `livecost1-iter-1` ran 172 shell commands (166
distinct, most of them reads of its own files) *with* the fold already in place, re-reading is not a
hypothetical. So the report's "medium confidence in the projection" understates the risk in the direction
that *supports its conclusion*: the windowed role may not just discard used content, it may not even stay
under the criterion. That makes the negative result stronger, not weaker.

Levers the spike does not consider (it is scoped to the window, so this is context, not a defect): the cost
term that dominates is **call count × re-sent history**, not the window's contents; the largest individual
messages are *tool observations* and whole-file write arguments, which are re-sent on every later call —
capping or summarising those, or keeping a **working set of the files currently in play**, attacks the cost
without recency; prompt caching is unmeasured (`cache_hit_tokens` is `null` in all four recordings); and
restructuring the pipeline so one Developer invocation is smaller changes the denominator rather than the
context. The report's §7 recommends the working-set direction but does not measure it.

## 6. The gate and the flake — **CONFIRMED**

Own build dir `F:/acc-hw-target`, one test process at a time, free disk checked before and after
(27,899 MB → 18,597 MB), no `rm -rf`, no wildcards, helper script outside the repository.

| check | command | result |
|---|---|---|
| test suite | `cargo test --offline` | **exit code 0**; **800 passed / 0 failed / 6 ignored / 806 listed**; 60 `test result:` lines; **0** `warning:` lines |
| names | `cargo test --offline -- --list` | exit 0, **806** names |
| ignored names | `cargo test --offline -- --list --ignored` | exit 0, **6** names |
| formatting | `cargo fmt --all --check` | exit 0, **0 bytes** of output |

Identical to the stated baseline 800 / 0 / 6 / 806, so **no test was removed**, and `listed = passed +
ignored` (806 = 800 + 6). `git status --porcelain` was empty before the gate; `HEAD` is
`8f06ce69b75496736ae7e410a27d051ac5e34c37`. The named flaky test,
`adapter::bevy::brp::tests::a_slow_reply_that_exceeds_the_timeout_is_a_timeout`, is present in the list and
is **not** ignored; it passed in my run.

**The disclosed first failing run I could not confirm.** The report says a first execution returned exit
101 with 440 passed / 1 failed / 0 ignored / 441 listed on that test. The spike's saved `gate.out` is the
*clean* run (60 `test result:` lines, 800 passed) and no log of the failing run survives in
`F:/spike-history-window/`, so the disclosure is honest but unverifiable from the tree. It does not affect
the gate verdict: the failure mode claimed (cargo stopping at the first failing target, 441 of 806 listed)
is consistent with the observed per-target listing order, and the flake is in a real-time timeout test.
I flag it as unverified, not as false.

---

## Defects

| id | severity | what | reproduction |
|---|---|---|---|
| **D1** | **high** | The byte-policy table, `max_bytes_passing_all_four = 49,152`, and the byte side of the sensitivity band (`32,768`) are wrong by 3.6×–5.8×. A faithful implementation of the stated policy passes at most **B = 13,543** (exclusive) or **B = 8,443** (inclusive). Cause: `F:/spike-history-window/final.py::window_bytes` accumulates a cumulative slice (`step = sum(b[pos[j-1]:bi])`) into an already-inflated `used`, so the loop stops early and the kept window is smaller than the policy names. Every byte row is therefore optimistic. | Run `python F:/acc-hw/deps_verify.py` / `bands.py`: they port the spike's `window_bytes` verbatim (reproducing its table) and the stated policy separately (giving 13,543 / 8,443). |
| **D2** | medium | `successful_project_write_events` is not project-only. The analysis counts every write event including `.hoh/scratch/**` script and note writes; only then filters to project paths for the edges. Reported 23 (iter-2) = **11** project writes + 12 scratch; reported 19 (iter-3) = **9** + 10; reported 1 (live) = **0** + 1. Only iter-1 (6) is all-project. The prose "6 / 23 / 19 / 1 successful project writes" overstates project writes up to 2×. | `python F:/acc-hw/deps_verify.py` prints `write_events(all)` and `project_only` side by side. |
| **D3** | low | The live rows rest on a `bytes → tokens` fit that does not hold: slope 0.2171, intercept 7,757.7, worst residual 7,008 tokens, per-call ratio 0.2518–0.7062. The report presents 0.323468 as a single calibration for them. The corrected byte band edge is decided by exactly these rows. | `python F:/acc-hw/fit.py`, `extras.py`. |
| **D4** | low | `iter_2_fit_total == iter_2_recorded_total` is offered as corroboration but is an identity of OLS with an intercept. | Algebraic; recomputed in `F:/acc-hw/fit.py`. |
| **D5** | low | The method note omits that 38 of the 296 round-4 "model calls" are user-role format-error retries carrying the failed response's usage (iter-1 20, iter-2 10, iter-3 8). The reconstruction is still correct, but a reader cannot tell this from the report. | `python F:/acc-hw/retries.py`. |

## Risks for the decision

* **The decision is still available, and it now points the same way.** The report's two headline bands are
  `4 steps` and `49,152 bytes`; the correct pair is `4 steps` and `~13.5 KiB` (or ~8.4 KiB). Both are far
  short of the recorded 28-step dependency, so the "band and dependencies do not overlap" argument holds on
  either number. The corrected number is *more* damning, not less.
* **The passing band is definition-sensitive and nearly marginless.** N = 4 passes iter-2 by 1.68 %; an
  implementation that counts the current step (the report's own caveat) is N = 5 ⇒ 1,631,524, a 1.09×
  overrun. A byte window has the same property between its two readings (13,543 vs 8,443, a 1.6× range).
  No bounded-history policy should be described as "passing" without stating which grain it counts.
* **No live confirmation exists.** Every passing row is arithmetic over recorded call sequences that the
  window would have changed. Given the 1.68 % headroom, the projection should be treated as an upper bound
  on the policy's attractiveness, not as the policy's cost.
* **The live recording cannot answer the content question** (its payloads are fold notes) yet it is the
  binding recording for the corrected byte band. A byte-window decision therefore rests on the one
  recording about which the least can be said.

## What I could not establish

* **The report's first, failing gate run** (exit 101, 440 / 1 / 0 / 441). No log survives; only the
  re-run's clean output is on disk. Disclosed by the report, unverifiable by me.
* **Any evidence of a live windowed run.** None exists in the tree, by design (offline spike).
* **What a windowed role would actually do.** The replay holds 69 / 125 / 102 / 150 calls fixed; the
  re-read hypothesis is argued, not measured. The 1.68 % / 3.67 % margins are the honest way to express
  that uncertainty.
* **The true project-write population for iter-2 and iter-3** beyond what the spike's own detector sees.
  My independent enumeration found the same *edge* set and gaps, but I did not reconstruct every
  script-mediated write, so I confirm the report's counts rather than claiming a stronger bound.
* **Whether every named "step" boundary is the harness's own.** The call set, counts and usage sums match
  the trajectories exactly; the internal phrasing about steps is the harness's, and I verified the
  consequences rather than the vocabulary.

## Files and commands used (all reproducible)

* `F:/acc-hw/measure.py` — per-call wire bytes, call locations, totals (reproduces the corpus table).
* `F:/acc-hw/fit.py` — least-squares and per-call ratio spread.
* `F:/acc-hw/verify2.py` — verbatim port of the spike's `window_bytes` vs the stated policy.
* `F:/acc-hw/deps_verify.py` — dependency edges and corrected byte bands.
* `F:/acc-hw/bands.py` — exact band edges by binary search and the margins.
* `F:/acc-hw/onlysource.py`, `F:/acc-hw/decisive.py` — the decisive case, from content.
* `F:/acc-hw/gate.sh`, `F:/acc-hw/gate_parse.py` — the independent gate.
* Spike's own artefacts read (read-only): `F:/spike-history-window/final.py`, `final.json`, `build.py`,
  `gate.out`, `list.out`, `list_ignored.out`, `fmt.out`.
