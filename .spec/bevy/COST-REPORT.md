# Bevy round-5 cost batch — report

**Scope.** Cut the per-call context growth and prove it on recorded trajectories; make the
repeated-action tripwire mean what its name says; close the acceptance's defect list
(`.spec/bevy/ACCEPTANCE-ROUNDS.md`); record the decisions. **No round was run** — no engine, no
game, no network, no model call. Everything below is code, tests, or arithmetic over
`runs/round4/**` and `runs/round2/**`, which are read and never written.

```json
{
  "schema": "hof-rs / bevy round-5 cost batch report",
  "produced_at": "2026-10-05",
  "branch": "bevy-core",
  "round_run_in_this_batch": false,
  "gate": {
    "command": "cargo test --offline",
    "exit_code": 0,
    "exit_code_source": "literal `$?` written to F:/hof-cost-logs/gate-after.exit",
    "passed": 754,
    "failed": 0,
    "ignored": 6,
    "listed": 760,
    "test_targets": 58,
    "warning_lines": 0,
    "list_command": "cargo test --offline -- --list",
    "list_exit_code": 0,
    "listed_equals_passed_plus_ignored": true,
    "start_tree_gate_measured_by_this_batch": {
      "passed": 734, "failed": 0, "ignored": 6, "listed": 740, "exit_code": 0,
      "source": "same build directory, before any edit (F:/hof-cost-logs/gate-before.out)"
    },
    "delta": {"passed": 20, "listed": 20, "removed": 0},
    "fmt_command": "cargo fmt --all --check",
    "fmt_exit_code": 0,
    "fmt_output_bytes": 0,
    "build_dir": "F:/hof-cost-target",
    "no_other_test_process": true
  },
  "context_measurement": {
    "method": "For each recorded model call, the message list the agent held before that call is reconstructed from runs/round4/iter-*/traj/developer.attempt1.json; the wire size is the same subset mini sends (role, content, tool_calls, tool_call_id), excluding the local-only `extra` blocks. The provider's own usage.prompt_tokens is fitted against that wire size by least squares over all 296 recorded calls. The repository's own hof_rs::harness::compact::compact_history then folds the same prefix and the compacted wire bytes are converted with the fitted ratio. No round is run and no formula is invented.",
    "fit": {
      "iter_2_slope_tokens_per_wire_byte": 0.255366,
      "iter_2_intercept": -38.28,
      "iter_2_fit_total": 12765478,
      "iter_2_recorded_total": 12765478,
      "iter_2_worst_call_residual_tokens": 1347,
      "total_reproduction_error": "<0.01%"
    },
    "dominated_by": "call count multiplied by accumulated history: 69/125/102 model calls re-sending 9.90 MB / 50.01 MB / 19.75 MB of wire bytes in total, with a final prompt of 46,801 / 161,566 / 66,002 tokens. The system prompt is 14,522 bytes of content (14,849 of wire; F-2: the earlier 14,783/14,814 was wrong) - about 9% of iter-2's final prompt, not the dominant term; per-call it is 4,269 of the first call and 14,849 of the 161,566-token last one. After the fold the system prompt is the largest single *fixed* item left (17.7% of the compacted wire bytes), though the preserved tail (34.1%) and the under-floor band (28.7%) are larger terms made of history.",
    "tail_curve_wire_bytes_iter_2": {
      "sent": 50007767,
      "tail_0": 7339794, "tail_2": 7877330, "tail_4": 8401914, "tail_6": 8933735,
      "tail_8": 9451685, "tail_12": 10503715, "tail_16": 11527568, "tail_24": 13601592,
      "tail_32": 15807809
    },
    "per_developer_call": {
      "before": {"iter_1": 2544563, "iter_2": 12765478, "iter_3": 5137090, "mean": 6819044,
                 "recorded_round_total": 20940837, "recorded_calls": 296, "recorded_minutes": 98.6},
      "after_tail_12": {"iter_1": 875647, "iter_2": 2681282, "iter_3": 1663325, "mean": 1740085,
                        "fraction_of_recorded": 0.2553},
      "per_call_before": {"iter_1": 46801, "iter_2": 161566, "iter_3": 66002, "mean": 72939},
      "per_call_after_tail_12": {"iter_1": 14920, "iter_2": 25152, "iter_3": 23705, "mean": 18300}
    },
    "projected_round": {
      "ac10_correction": "This block was not like-for-like: the old `before` figure (20,940,837) included completion tokens while the old `after` figure (5,219,854) was prompt-only, so the quoted 25.5% understated the prompt reduction and the three after-figures actually sum to 5,220,254. Both halves are stated like-for-like here.",
      "measured_developer_prompt_before": 20447131,
      "projected_developer_prompt_after": 5220254,
      "projected_prompt_reduction": 0.7447,
      "completion_tokens_unchanged": 493706,
      "projected_developer_total_after": 5713960,
      "measured_developer_total_before": 20940837,
      "projected_total_reduction": 0.7271,
      "scope_of_the_projection": "the Developer role only: the three recorded Developer calls are the trajectories this batch measured. The round's other roles were not measured and are not claimed."
    },
    "changed": "src/harness/compact.rs (new): fold superseded history at the send point, keep the system prompt, the task and the last compact_history_tail=12 messages verbatim; whose result is what the trajectory records. src/harness/mini.rs: the loop is ours (mini's run cannot fold between steps); step counting moved into the same loop. src/config.rs: compact_history=true, compact_history_tail=12."
  },
  "tripwire_now": {
    "fires_on": "one action key succeeding max_repeated_actions (15) times in a row with a BYTE-IDENTICAL result, since the call last wrote the artifact it declares",
    "does_not_fire_on": "a run of the same command whose results differ - i.e. work that is still producing new information (round 4: 16/15/17 such repeats in the measured windows, none byte-identical)",
    "round_4_evidence": "the measured window maximum for 'cargo build --offline' was 16 (iter-1), 15 (iter-2), 17 (iter-3) by the round-4 count, but at most 2 with identical results. Under the new rule none of the three calls would be aborted by this counter at all.",
    "round_2_control": "the recorded grind (runs/round2/iter-1) reaches 22 repeats in the same window; its results also differ (only 2 identical), so the round-5 counter does not fire on it either - the honest statement is that this counter is a guard against a call whose result has stopped changing, not a cost control.",
    "can_it_still_end_a_progressing_call": "no, not on a call that is making progress on its artifact: a counted write clears the run, and any changed result restarts it. A call that writes nothing and gets the same answer 15 times is the only shape it ends.",
    "renamed_status": "unchanged (RepeatedActionError); the message now states the rule it applied",
    "pinned_by": ["harness::guard::tests::a_repeated_action_whose_result_changes_is_not_unproductive_repetition", "harness::guard::tests::a_repeated_action_whose_result_stops_changing_is_still_aborted", "harness::guard::tests::the_same_successful_action_repeated_to_its_cap_aborts_the_call", "tests/repeated_action.rs"]
  },
  "defects": [
    {"id": "criterion-4-cost", "disposition": "partially closed: projected per-call Developer **prompt** tokens 72,939 -> 18,300 and the three recorded calls 20,447,131 -> 5,220,254 prompt tokens (74.47% of the recorded prompt spend; adding the unchanged completion tokens back gives 5,713,960 against 20,940,837, i.e. 72.71%). AC-10: the earlier '20.94M -> 5.22M (25.5%)' mixed prompt+completion on the before side with prompt-only on the after side. The 1.5M-per-call target is NOT reached (iter-2 projects to 2,681,282 prompt + 325,953 completion = 3,007,235, over 2x the target; F-1: the earlier 3,034,063 was an arithmetic slip - 2,681,282 + 325,953 = 3,007,235, which is what FIX-REPORT and this report's own projected_round block give), and no round was run to confirm the projection on a live call. FIX-REPORT.md §5 measures the fold's own floor: even with the verbatim tail removed entirely, iter-2 projects to 1,873,629 prompt tokens. That floor bounds only the fold's own family (every superseded message replaced by a note); a policy that kept nothing but the system prompt and the task would project to 517,368 prompt + 325,953 completion = 843,321 for iter-2, far below the target - which is the trade the batch refuses, not an impossibility (see F-3 in FIX-REPORT.md §5)."},
    {"id": "unverified-item-tripwire-at-15", "disposition": "fixed: the counter now requires identical results and a write-free window; tested; round 4's three calls would no longer be ended by it."},
    {"id": "RA-1", "disposition": "fixed: the ledger is written after the spawn (a pid cannot exist before it); the append_ledger and ledger_entry docs, the call-site comment, the entry's own `note`, reap_ledger's doc and ROUND-4-REPORT-COMPLETE.md now say so. The nonce really is generated before the spawn and that is stated as the surviving proof. Pinned by adapter::bevy::launch::tests::the_ledger_line_is_written_after_the_spawn_and_says_so."},
    {"id": "RA-2", "disposition": "fixed: the e3_grounded_payload proving_reading in .spec/bevy/ROUND-4-REPORT-COMPLETE.md cited frame 477, which runs/bevy-round4/calls/0008-bevy_grounded.json does not contain; the file's own FrameCounter value is 495 and the line now says 495 and names the file it was read from."},
    {"id": "RA-3", "disposition": "fixed at the source: round-stop.json now carries ledger_lines_at_sweep and a sweep_covers_ledger_line(line) predicate, so a snapshot of the directory can answer 'does this sweep cover my pass's launch' from the file itself (it does not, when the pass launched after the sweep). Pinned by the round-stop sweep test."},
    {"id": "RA-4", "disposition": "fixed: identity.verified is now the conjunction of (1) a non-empty nonce, (2) the NEW answered_nonce field equalling it (what readiness read back over the wire), and (3) the OS TCP table naming spawned_pid as the listener. verified_game_endpoint no longer writes Some(true). AC-4 correction: the earlier claim 'six cases pinned, each false for a launch that really occurs' was false. Terms (1) and (2) are invariants of every launch that *returns* — `launch.rs:502-529` sets answered_nonce only on the equality arm, and a mismatch returns LaunchError::IdentityMismatch and stops the child, so no LaunchFacts exists — hence those cases can only be built by hand. The field's discriminating power for a real launch is term (3), the operating-system listening reading, alone (the exact property D298's option 4 rejected and D301 revisits). Pinned: the field is false when the OS listener is another pid or is absent, and the mismatched/absent answered_nonce cases are hand-built and labelled as impossible for a returned launch."},
    {"id": "RA-5", "disposition": "fixed (found while auditing the defect list): the derived PRD-coverage line and PrdCoverage::label now say in the line itself that the denominator is the Tester's own claim count and not F1..F17, and that the figure is not comparable between rounds."},
    {"id": "RA-6", "disposition": "fixed: src/prompts/skills/godot-dev.md (17,451 B) and godot-testing.md (5,160 B) are removed from the tree and from prompts::skills(); they were compiled in and delivered into every round workspace. The prompt-discipline tests that read them now read bevy-dev.md / bevy-testing.md and the Bevy books gained the two sentences those rules check (the audience ruling; a concrete tools-call recipe; a scratch-discipline section), so coverage is kept rather than deleted."},
    {"id": "RA-7", "disposition": "closed, and the earlier disposition was inaccurate: RA-7 ('DECISIONS.md has no round-3 / round-4 entry') IS present at .spec/bevy/ACCEPTANCE-ROUNDS.md:137, which this batch's copy contained all along. It is closed in substance by D299 (the rounds 3-4 entry) and D300 (this batch). AC-5 correction: the previous text said the defect 'could not be located in this batch's copy of ACCEPTANCE-ROUNDS.md', which was false and understated what the batch did."},
    {"id": "RA-8", "disposition": "fixed by labelling: e3_win_position and e3_grounded_payload carry definitional=true plus their reason in the Observation, and the round's own record prints '[definitional: ...]' for them, so a reader counting behavioural proofs is not misled. Pinned by adapter::bevy::round::tests::the_definitional_battery_steps_say_so_in_the_rounds_record."},
    {"id": "RA-9", "disposition": "fixed: parse_listener_pid no longer falls back to the first non-LISTEN row; a localised/unknown state word yields None rather than a pid. Pinned by adapter::engine::tests::a_non_listening_holder_of_the_port_is_not_reported_as_the_listener."},
    {"id": "resume", "disposition": "implemented with a stated scope: an iteration whose result.json says ok:true is not re-run (its usage, gate and version are carried into the summary); the first incomplete iteration runs FROM ITS START. hoh run --resume refuses a missing run directory and is mutually exclusive with --fresh-workspace/--reset-workspace. A call interrupted mid-flight is NOT resumable at a finer grain and the code says why: the harness has no role-level checkpoint and a Developer edits the workspace in place."},
    {"id": "brp_connection_pool-cfg-windows", "disposition": "fixed: a_client_rebuilt_for_the_new_process_succeeds_on_its_first_call now carries the same cfg!(windows) guard as its sibling, with the reason (the abortive close the fixture needs is Windows-only), so it cannot fail on a platform where the product is fine."},
    {"id": "DECISIONS.md", "disposition": "appended only: D298 (the trust batch: nonce identity, endpoint attribution, ledger sweep, staged image, measured context formula, credential handling), D299 (rounds 3-4: the step budget at the point of work, the unit of a step, the folded action key, the write-restart, the computed identity fields), D300 (this cost batch, including what is declared rather than fixed). Verified append-only: the first 11268 lines hash to the same md5 as HEAD's DECISIONS.md (04b816fd088f808b1d70cd19cc7158be); the file grew 11268 -> 11414 lines."}
  ],
  "plants": [
    {"id": "P1_context_fold_disabled", "file": "src/harness/compact.rs", "what": "the fold's early return is short-circuited to true", "green_before": 0, "red": 101, "green_after": 0, "restore_byte_exact": true, "sha256": "64de990c5a7a396cf08661ac0f80f4af6eec39cf39573dd2034a02c7e434fcd9"},
    {"id": "P2_repetition_ignores_the_result", "file": "src/harness/guard.rs", "what": "RepeatRun::record_repeat counts every success of the key again, i.e. the round-4 rule", "green_before": 0, "red": 101, "green_after": 0, "restore_byte_exact": true, "sha256": "4225c53e38d79f6a9038930e308155778062e4c1dd6b0766d6a69bcc61558692"},
    {"id": "P3_identity_verified_is_the_nonce_alone", "file": "src/adapter/bevy/round.rs", "what": "verified: nonce_proved (the RA-4 shape)", "green_before": 0, "red": 101, "green_after": 0, "restore_byte_exact": true, "sha256": "7ed710af965366ed50d49cd92bd56f0343c305a2425e8ae2f9fdc53cb722b27d"},
    {"id": "P4_listener_parse_falls_back_to_a_holder", "file": "src/adapter/engine.rs", "what": "parse_listener_pid returns the matching row whatever its state (the RA-9 shape)", "green_before": 0, "red": 101, "green_after": 0, "restore_byte_exact": true, "sha256": "1321fac0bc80d1ccd6444619a4f349e3d70fa359107f20a4371c771938f001fc"}
  ],
  "changed_files": {
    "added": ["src/harness/compact.rs", "tests/context_compaction.rs", "tests/resume_round.rs"],
    "modified_core": ["src/adapter/bevy/battery.rs", "src/adapter/bevy/launch.rs", "src/adapter/bevy/mod.rs", "src/adapter/bevy/project.rs", "src/adapter/bevy/round.rs", "src/adapter/engine.rs", "src/cli.rs", "src/cli_impl.rs", "src/config.rs", "src/errors.rs", "src/harness/guard.rs", "src/harness/mini.rs", "src/harness/mod.rs", "src/model.rs", "src/prompts/mod.rs", "src/prompts/skills/bevy-dev.md", "src/prompts/skills/bevy-testing.md", "src/runtime/hygiene.rs", "src/runtime/role.rs", "src/runtime/run_loop.rs"],
    "modified_tests": ["tests/artifact_hygiene.rs", "tests/brp_connection_pool.rs", "tests/common/mod.rs", "tests/delivered_materials.rs", "tests/developer_contract.rs", "tests/e1_increment.rs", "tests/evidence_isolation.rs", "tests/evidence_unreachable.rs", "tests/prd_coverage.rs", "tests/prompt_shell_contract.rs", "tests/repeated_action.rs", "tests/result_semantics.rs", "tests/role_paths.rs", "tests/tool_discovery.rs"],
    "removed": ["src/prompts/skills/godot-dev.md", "src/prompts/skills/godot-testing.md"],
    "reports": [".spec/bevy/ROUND-4-REPORT-COMPLETE.md (one false frame citation corrected, RA-2)", "DECISIONS.md (appended only)"],
    "tests_removed": 0
  },
  "not_verified": [
    "The projection is arithmetic over recorded trajectories. No round was run, so no live call confirms that the fold produces the projected prompt tokens or that the role still behaves well with 12 verbatim messages.",
    "The model's behaviour under folded history is unmeasured: a role may re-read a file it was told it had already written, because the fold replaces the payload with a digest. The stored evidence (the write result, the digest) is still there, and the file is on disk, but this is a real behavioural risk of the change and it was not testable offline.",
    "--resume has not continued a real interrupted round: the decision is pinned as arithmetic over a built run directory, and the loop's skip/continue path is not exercised end to end (that needs a run).",
    "The 1.5M-token-per-call target is not reached on this projection (per-call developer mean 18,300; three calls 5.22M). No *tail value of this fold* reaches it, and the batch's own tail-0 figure bounds only that family: a context-only policy that dropped consumed pairs outright, or kept only the system prompt and the task, would project to 287,657 / 517,368 / 430,085 prompt tokens for the three recorded calls (369,289 / 843,321 / 516,206 with completion) and would pass - what is refused is that trade (the role no longer sees the history it works from), not an impossibility (F-3). The remaining *capability-preserving* lever is the call count.",
    "Round 4's own report prose is frozen; only the RA-2 citation line was corrected. Whether other prose in ROUND-4-REPORT*.md is stale was not audited.",
    "The acceptance's RA-7 is present at .spec/bevy/ACCEPTANCE-ROUNDS.md:137 and is closed in substance by D299 (rounds 3-4) and D300 (this batch); the earlier 'not located' disposition was wrong (AC-5)."
  ],
  "single_most_important_thing_next_batch": "Re-run the cost measurement on one real Developer call before trusting the projection, and read the trajectory for the two things the fold cannot show offline: whether the role re-derives anything it no longer sees, and the real prompt tokens per call against the projected 18,300. The fold is the only change in this batch whose risk is behavioural rather than mechanical; every other item is pinned by a test that fails when the behaviour is removed."
}
```

## 1. What changed, and what pins it (per mechanism)

### 1.1 The per-call context growth — `src/harness/compact.rs` (new)

**The measurement.** Over the three recorded round-4 Developer calls the prompt is the accumulated
history, re-sent on every model call: 69/125/102 calls re-sent 9.90 MB / 50.01 MB / 19.75 MB of wire
bytes in total, for 2,544,563 / 12,765,478 / 5,137,090 prompt tokens and a final prompt of 46,801 /
161,566 / 66,002. The content is dominated by **superseded payloads**: a tool call whose
`arguments` carry the whole of `src/game.rs` (22–32 KB, recorded at `api=136` in iter-2 and elsewhere),
and tool results that dumped a file. Once an action has run, that text has been consumed — the file is
on disk and the fact is in the model's own next action — and re-sending it buys nothing.

**The change.** `compact_history` folds superseded messages at the **send point**:
the system prompt and the task are never touched; the last `compact_history_tail` (12) messages are
never touched; everything older becomes a first line plus a sha256/byte-count note. A tool call keeps
its `tool_calls` shape and its call ids (the provider validates the pairing) and replaces only the
argument text; a tool observation keeps its `<returncode>`. The fold runs on the agent's own history,
so the trajectory records exactly what was sent.

**The method, and why it is not a formula.** For every recorded call the prefix the agent held is
reconstructed and its wire size computed with the same subset mini sends (role, content, tool_calls,
tool_call_id — the local `extra` blocks never leave the process). The provider's own
`usage.prompt_tokens` is fitted by least squares against that size: `r = 0.255366` tokens per wire byte
for iter-2, reproducing the call's own total to **<0.01%** (12,765,478 fitted vs 12,765,478 recorded;
worst single-call residual 1,347 tokens). The repository's own `compact_history` then folds the same
prefix, and the compacted bytes are converted with that measured ratio. `tests/context_compaction.rs`
is that measurement as a test: it asserts the fold shrinks every recorded call, that it can never grow
one, and that the curve is monotone in the tail.

| record | model calls | prompt tokens before | projected after (tail 12) | per call before | per call after |
|---|---|---|---|---|---|
| round-4 iter-1 | 69 | 2,544,563 | 875,647 | 36,878 | 12,691 |
| round-4 iter-2 | 125 | 12,765,478 | 2,681,282 | 102,124 | 21,450 |
| round-4 iter-3 | 102 | 5,137,090 | 1,663,325 | 50,364 | 16,307 |

(The last two columns are means: `tokens / calls`. The last call's own prompt falls from 46,801 /
161,566 / 66,002 to 14,920 / 25,152 / 23,705, i.e. the final prompt is smaller than the *mean* was
before — the growth term is what the fold removes.)

Projected developer spend for the three calls, **prompt to prompt**: 20,447,131 → 5,220,254 (25.53%,
i.e. a 74.47 % reduction); adding the unchanged completion tokens (493,706) back to the projected
prompt gives 5,713,960 against the 20,940,837 recorded total, a 72.71 % reduction.  (AC-10: the
earlier "20,940,837 → 5,219,854 (25.5%)" compared a prompt+completion *before* with a prompt-only
*after*, and the three after-figures sum to 5,220,254.)  The per-call mean falls from 72,939 to about
18,300 prompt tokens, and the last call's prompt from 161,566 to 25,152. Against the recorded 296
calls / 20,940,837 developer tokens / 98.6 minutes, that is a projected saving of ~15.2M developer
tokens and about 25 minutes of model time **for the Developer role only** — the other roles were not
measured and are not claimed.

**What dominates after the fold.** The system prompt: 14,849 wire bytes (14,522 of content; defect
**F-2** — the earlier 14,783/14,814 contradicted this report's own composition), unchanged, which is
17.7 % of the compacted wire bytes and 3,791 of the compacted final call's 25,152 projected prompt
tokens (15.1 %, at the measured 0.2553 tokens/byte) instead of about 9 %. It is the largest single
*fixed* term — the one re-sent unchanged on every call — but not the largest term left: the preserved
tail (34.1 %) and the under-floor band (28.7 %) are bigger, and both are history the fold chose not to
drop. That is the honest reading, and it is why the remaining lever is the call count rather than the
fixed prompt.

### 1.2 The tripwire — `src/harness/guard.rs`

It used to count **every** success of one action since the call last wrote its declared artifact, and
it fired at exactly 15 on all three round-4 Developer calls — always after a valid artifact had been
written and the version advanced. The measured window maxima were 16 / 15 / 17 for
`cargo build --offline`, and the results were **not** identical (successive runs printed 225, 130, 354,
… bytes), which is what made it arbitrary.

It now counts **only consecutive successes with a byte-identical result** since the last counted write.
A changed result restarts the run; a counted write clears it. So:

* work that is still producing new information is never ended by it — round-4's three calls would not
  be aborted at all under the new rule (identical-result maximum: 2);
* a call that writes nothing and gets one unchanged answer will be ended, and the abort message now
  states the rule it applied ("succeeded N times with the SAME result … the result is byte-identical
  every time, so no further run of it can change anything");
* the recorded round-2 grind is also not identical-result repetition (maximum 2), so this counter does
  **not** catch it either — the honest statement is that it is a guard against a call whose result has
  stopped changing, not a cost control.

Pinned by the two new guard tests (changed results allowed; identical results still aborted) plus the
existing cap test, whose message assertion was updated to the new wording.

### 1.3 The defects

* **RA-1** — the ledger is appended after the spawn (a pid cannot exist before it). The `append_ledger`
  and `ledger_entry` docs, the call-site comment, the entry's own `note`, `reap_ledger`'s doc and
  `ROUND-4-REPORT-COMPLETE.md` now state that ordering, and state that the **nonce** is the value
  generated before the spawn. New test `the_ledger_line_is_written_after_the_spawn_and_says_so`
  spawns a real child and asserts both halves.
* **RA-6** — `godot-dev.md` (17,451 B) and `godot-testing.md` (5,160 B) are deleted from the tree and
  from `prompts::skills()`. The tests that read them now read the two Bevy books: the delivered-form
  needles, the ≥7-recipe count, the executable first recipe, the scratch writer and the audience rules
  were all **moved**, not deleted. The Bevy books gained the two sentences those rules check, and the
  "Tester keeps the game-process recipe" assertion was re-pointed at concrete `bevy_*` tools (the old
  `running_game_<tool>` needle would have been vacuously true in the Bevy book — a needle that cannot
  fail is not coverage).
* **RA-2** — the `e3_grounded_payload` citation named frame 477; `runs/bevy-round4/calls/0008-bevy_grounded.json`
  contains 495 and is now named in the citation.
* **RA-3** — `round-stop.json` gains `ledger_lines_at_sweep` and `sweep_covers_ledger_line(line)`, so a
  snapshot can say from its own content that the sweep it carries does **not** cover a pass that
  launched after it.
* **RA-4** — `identity.verified` becomes the conjunction of three recorded readings, and `launch.json`
  gains `answered_nonce` (the value readiness actually read back). `LaunchFacts` carries it;
  `verified_game_endpoint` no longer hard-codes `Some(true)`.
* **RA-5** (found while auditing the list) — `prd coverage: 6/8` now says in the line that 8 is the
  Tester's own claim count, not the PRD's F1..F17, and that it is not comparable between rounds.
* **RA-8** — `e3_win_position` and `e3_grounded_payload` are labelled `definitional` with their reason
  in the observation **and** in the round's own record text.
* **RA-9** — `parse_listener_pid` returns only a `LISTEN*` row; an unknown (localised) state yields
  `None`. The old localised-state test asserted the fallback behavior, and now asserts the opposite
  with the reason.
* **`--resume`** — implemented with an explicitly limited scope (see §3).
* **`cfg!(windows)`** — the second `brp_connection_pool` test now carries the guard its sibling has,
  with the reason: the fixture's abortive close is Windows-only, so without it the test would fail on
  a platform where the product is fine.

### 1.4 `DECISIONS.md`

Appended only, three entries: **D298** (the trust batch — nonce identity, endpoint attribution, ledger
sweep, staged image, the measured cost formula, credential handling), **D299** (rounds 3–4 — the step
budget at the point of work, the unit of a step, the folded action key, the write-restart, the computed
identity fields) and **D300** (this batch, including the list of things declared rather than fixed).
Verified append-only: the first 11,268 lines hash to the same md5 as `HEAD:DECISIONS.md`
(`04b816fd088f808b1d70cd19cc7158be`); the file grew to 11,414 lines.

## 2. Plants

Four controlled plants, each green → red → green with a byte-exact restore and an mtime set
explicitly (a newer one after the restore, so cargo cannot skip the rebuild):

| plant | file | the planted defect | green before | red | green after | restore |
|---|---|---|---|---|---|---|
| P1 | `src/harness/compact.rs` | the fold is short-circuited off | exit 0 | **exit 101** | exit 0 | byte-exact |
| P2 | `src/harness/guard.rs` | every success counts again (round-4 rule) | exit 0 | **exit 101** | exit 0 | byte-exact |
| P3 | `src/adapter/bevy/round.rs` | `verified: nonce_proved` (the RA-4 shape) | exit 0 | **exit 101** | exit 0 | byte-exact |
| P4 | `src/adapter/engine.rs` | `parse_listener_pid` falls back to a holder | exit 0 | **exit 101** | exit 0 | byte-exact |

In every run the child reported `test result:` (so the test really ran, rather than the crate failing
to compile), and the red run named the intended assertion. The restored sha256 of each file equals the
captured one; each restore's mtime was set explicitly and re-read. Logs and the machine-readable record
are in `F:/hof-cost-logs/plants.json` and `F:/hof-cost-logs/P*.log`.

## 3. `--resume`: what it does and what it refuses

`hoh run --resume --run-id <id>`:

* refuses a run directory that does not exist, and is mutually exclusive with `--fresh-workspace` and
  `--reset-workspace`;
* **does not re-run** an iteration whose `runs/<id>/iter-<n>/result.json` carries `ok: true`; that
  iteration's usage, gate and version are read back and carried into this run's summary, and no model
  call is made for it;
* runs the **first incomplete** iteration **from its start**;
* records what it did in the round's warnings (`resumed_from_interrupted_round`), including the
  sentence that says why a finer grain is not offered.

**What it refuses, and why.** It does not resume inside a role call. The harness has no role-level
checkpoint: a Developer edits the workspace *in place* through the write directive, and a `result.json`
is written only at the end of an iteration, so there is no point inside a call at which a half-finished
increment could be handed to a fresh call without either replaying work or pretending work exists. A
~90-minute attempt is therefore recoverable at the cost of the one incomplete iteration, not for free —
and the report says so rather than shipping a fake finer-grained resume.

The decision is arithmetic over a run directory and is pinned offline by `tests/resume_round.rs`
(completed / missing / failed / hole / fully-complete / empty cases).

## 4. What I could not verify

Every one of these is a limit of an offline batch, not a hedge:

1. **No live call confirms the projection.** The fold's effect is measured on recorded trajectories
   and the repository's own fold function; whether a real Developer call produces the projected
   prompt tokens is untested, because testing it needs a round.
2. **The role's behaviour under folded history is unmeasured.** A model that no longer sees a payload
   it was told it had already written may re-read the file. The write result and the digest remain in
   the history and the file is on disk, but this is a genuine behavioural risk of the change and it
   cannot be settled offline.
3. **`--resume` has not continued a real round.** The skip/re-run decision is pinned; the loop's
   continue path over a real interrupted run is not.
4. **The 1.5M-token-per-call target is not reached** (projected developer mean 18,300 prompt tokens;
   three calls 5.22M prompt). The remaining capability-preserving lever is the call count, not the
   context: no tail value of this fold reaches the target (with the verbatim tail removed entirely,
   iter-2 still projects to 1,873,629 prompt tokens), but the tail-0 figure bounds only the fold's own
   family — a policy that kept nothing but the system prompt and the task would project to 517,368
   prompt + 325,953 completion = 843,321 for iter-2 and **would** pass, at the cost of the history the
   role works from. What is refused is that trade, not an impossibility (defect **F-3**). See
   FIX-REPORT.md §5.
5. **The frozen round-4 report prose was not audited**, only the one false citation corrected.
6. **RA-7 is present at `.spec/bevy/ACCEPTANCE-ROUNDS.md:137`** and is closed by D299/D300; the
   earlier "no distinct entry" disposition was wrong (AC-5).

## 5. The single most important thing for the next batch

Re-run the cost measurement on **one real Developer call** before trusting any of this, and read that
trajectory for the two things an offline batch cannot show: whether the role re-derives anything the
fold no longer sends it, and the real prompt tokens per call against the projected 18,300. The fold is
the only change in this batch whose risk is behavioural rather than mechanical; everything else is
pinned by a test that goes red when the behaviour is removed.
