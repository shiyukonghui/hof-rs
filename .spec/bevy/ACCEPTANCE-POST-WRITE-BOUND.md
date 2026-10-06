```json
{
 "schema": "hof-rs / bevy post-write call bound: independent acceptance",
 "artifact": ".spec/bevy/ACCEPTANCE-POST-WRITE-BOUND.md",
 "subject": ".spec/bevy/POST-WRITE-BOUND-REPORT.md (implementation commit e900262, on b6e9364)",
 "produced_at": "2026-10-06",
 "reviewer": "fresh independent acceptance subagent; no implementer context inherited",
 "verdict": "pass",
 "verdict_basis": "The mechanism is wired in the production path and quoted from the code; the off-by-one (a bound B allows B calls and bills B+1) is confirmed both from `steps > budget` and from the recorded unwritten round that billed 44 calls at budget 43. Every prefix sum was re-derived from the recordings and reproduces the report exactly, including the binding recording (round4-iter-3: 1,452,307 at 36 billed calls, 0.968x; 1,502,443 at 37, 1.002x, over by 2,443). The bound is genuinely unreachable before a write, and the non-weakening claims hold (write guarantee, unwritten allowance and NoEngineeringWrite gate unchanged; no test removed). The gate reproduces: cargo test --offline exit 0 with 824 passed / 0 failed / 6 ignored / 830 listed, cargo fmt --all --check exit 0, 0 compiler warnings. Two errors were found inside the artefact's projection tables and are recorded as defects; neither touches the binding arithmetic or the headline claim, which is restricted to the six recorded producing calls.",
 "gate": {
  "cargo_test_offline": {
   "literal_exit_code": 0,
   "passed": 824,
   "failed": 0,
   "ignored": 6,
   "listed": 830,
   "test_result_lines": 62,
   "compiler_warning_lines": 0,
   "error_lines": 0
  },
  "cargo_test_list": {
   "literal_exit_code": 0,
   "count": 830
  },
  "cargo_test_list_ignored": {
   "literal_exit_code": 0,
   "count": 6
  },
  "cargo_fmt_all_check": {
   "literal_exit_code": 0,
   "stdout_bytes": 0,
   "stderr_bytes": 0
  },
  "build_dir": "G:/pwb-accept-target (own dir; repository target/ unused; F: had 8.2 GiB free, G: 358 GiB)",
  "one_test_process_at_a_time": true,
  "test_attr_count_b6e9364": 819,
  "test_attr_count_head": 830,
  "per_file_delta": {
   "src/harness/guard.rs": "29 -> 34",
   "tests/post_write_bound.rs": "0 -> 6",
   "all other files": "unchanged"
  },
  "test_source_numstat_tests_dir": {
   "tests/post_write_bound.rs": {
    "added": 472,
    "deleted": 0
   }
  }
 },
 "criteria": [
  {
   "id": "C1",
   "question": "The budget mechanism and the bound's semantics: what counts as a step, where the budget is computed, where enforced, the off-by-one, and that the value reaches enforcement in production.",
   "pass": true,
   "evidence": "A step is a model call: src/harness/compact.rs:302 `self.progress.steps.increment();` inside CountingModel::query, handed to the guard by src/harness/mini.rs:128 `.sharing_steps(steps)`. Computed in src/config.rs AgentLimits::effective_step_limit (lines 329-338) which returns `written_step_limit()` when has_written, and written_step_limit() = `if post_write_step_limit == 0 { step_limit } else { post_write_step_limit.min(step_limit) }`. Enforced at src/harness/guard.rs:868-881 step_budget_exceeded(): `let budget = self.effective_step_budget().min(self.step_limit); let steps = self.steps(); if steps > budget {...}`, called as the first statement of execute (guard.rs:1112). effective_step_budget() (guard.rs:809-811) = `self.limits().effective_step_limit(self.artifact_written())`, so the bound is a function of the live artifact_written flag. Production wiring: config/hoh.yaml `agent.post_write_step_limit: 35` -> load_config take_section -> HohConfig.agent -> run_loop RoleInvocation { limits: cfg.agent.clone() } -> mini.rs:133 `.with_post_write_step_limit(inv.limits.post_write_step_limit)` -> WriteGuardEnvironment.post_write_step_limit -> limits() -> effective_step_budget(). Off-by-one: `steps > budget` with the counter incremented before the request is forwarded means the 1..=B calls act and the B+1-th is billed then refused; the recorded unwritten round runs/completion1/iter-3 billed 44 calls at budget 43 with exit_status StepBudgetExceeded (hoh.usage.calls=44, 44 response-bearing messages, 803,027 tokens), which I re-read from the file."
  },
  {
   "id": "C2",
   "question": "The compatibility argument: the bound unreachable before a write, and the arithmetic at the window's edges (33-35).",
   "pass": true,
   "evidence": "Structural half: the only enforcement read is effective_step_budget(), which calls effective_step_limit(artifact_written()); artifact_written is set to true only by a successful directive write whose path is not excluded (guard.rs:1035-1048 via ArtifactKind::ProjectFile::counts -> !is_excluded_path), and the guard instance is built per call inside MiniHarness::invoke, so it starts false. A call that has not written therefore always gets 25 + max(150/8,1) = 43 and can never see 35; pinned by the new test the_unwritten_guard_is_untouched_by_the_post_write_bound (refused at steps==44 with 'live step budget is 43') and the MiniHarness control a_call_that_has_not_written_keeps_the_unwritten_allowance (6 calls at unwritten 5 while the bound is 3). Arithmetic half: I prefix-summed each recording's own extra.response.usage.total_tokens over every response-bearing message (94 assistant + 8 user messages in round4-iter-3; my sum 5,223,211 equals hoh.usage.total_tokens exactly for all seven recordings). Binding recording round4-iter-3: P(36)=1,452,307 (0.9682x, headroom 47,693 = 3.18%), P(37)=1,502,443 (1.0016x, over by 2,443). B=35 bills 36 calls -> under; B=36 bills 37 -> over. Lower end: under a flat reading B>=33 is needed so round4-iter-2's first write at call 33 is not cut (I re-derived first project writes 7/33/6/6 and 8/13); structurally any B satisfies it, which the report states. Window 33-35 confirmed, with the lower end labelled as flat-reading-only."
  },
  {
   "id": "C3",
   "question": "The projections: re-derive every figure; is 'every recorded producing Developer call lands under the criterion' true; is combining the bound with the recorded exits legitimate or double counting.",
   "pass": true,
   "evidence": "All seven recordings' per-call sequences and prefix sums were re-derived independently and reproduce the report exactly: r4-i1 P(26)=705,441 / P(36)=1,127,441 / P(44)=1,476,168 / P(45)=1,521,112 and max under 44; r4-i2 P(26)=684,879 / P(36)=1,196,549 / P(40)=1,496,626 / P(41)=1,568,638 and max 40; r4-i3 as above; livecost1 P(36)=558,945 / P(81)=1,484,934 / P(82)=1,511,382 / max 81; live-i1 P(36)=579,120 / P(78)=1,480,801 / P(79)=1,503,171 / max 78; live-i2 P(36)=633,893 / P(74)=1,484,574 / P(75)=1,508,821 / max 74; live-i3 P(44)=803,027. Write calls, first project writes and the project/scratch split also reproduce exactly (7/33/6/6 and 8/13; r4-i2 project 33,35,36,37,42,44,46,55,65,67,72 and scratch 27,29,40,63,64,69,71,97,99,106,109,116), as do the first declared finishes 25/58/30 and null for the live four. At B=35 all six producing calls are under (0.752x / 0.798x / 0.968x / 0.373x / 0.386x / 0.423x), so the headline claim is true as stated. The min(bound, first legitimate exit) combination is legitimate, not double counting: the two are stopping rules and the call ends at whichever fires first, and calls 1..min are unaffected because before a write the enforced budget is 43 (>36) and after a write the write already exists. One table error: the combined table's live-completion1-iter-3 row claims 36 calls / 654,384 tokens, but that call never wrote, so the bound cannot apply; the correct row is 44 calls / 803,027 as the report's own bound-alone table says. See defect D1."
  },
  {
   "id": "C4",
   "question": "What it does not cover: the wrap-up retry a bound-cut unlaunchable artifact could trigger, and the dependency on a counted directive write.",
   "pass": true,
   "evidence": "Retry verified from the code: src/runtime/invoke.rs:268-276 is_limits_exceeded accepts StepBudgetExceeded; src/runtime/run_loop.rs:1708 `developer_limits = is_limits_exceeded(...)`, 1718 the adapter's developer_artifact_valid, 1735 `if developer_limits && !developer_artifact_valid` with 1740 `wrap_base.limits.step_limit = cfg.agent.wrap_up_steps.min(WRAP_UP_RETRY_MAX_STEPS)` = min(25,30) = 25 and post_write_step_limit inherited 35, so the retry's written budget is min(35,25)=25 -> at most 26 billed calls. Magnitude: the recorded 26-call prefixes are 382,298 / 394,761 / 427,744 (live) and 684,879 / 705,441 / 971,219 (round-4), so a second call adds roughly 0.38M-0.97M tokens to the round's Developer stage; it did not fire in any recorded iteration (no developer.attempt2.json in runs/completion1/iter-*/traj/, and hoh.artifact_valid is true in all seven recordings, including the zero-write iter-3). Directive-write dependency verified: artifact_written is set only in execute_write for a non-excluded path; a shell-side project write leaves it false, so the budget stays 43 and the bound never engages. The report discloses both, and recorded live-completion1/iter-3 is a concrete instance of shell-side scratch activity with zero counted writes."
  },
  {
   "id": "C5",
   "question": "No weakening: write guarantee and unwritten allowance unchanged, a round writing nothing still fails, no removed/weakened test, and the reworded note/message accurate.",
   "pass": true,
   "evidence": "git diff b6e9364 e900262 touches only src/config.rs, src/harness/guard.rs, src/harness/mini.rs, config/hoh.yaml, tests/post_write_bound.rs, DECISIONS.md and .spec/bevy/POST-WRITE-BOUND-REPORT.md; src/runtime/** (including the NoEngineeringWrite gate at run_loop.rs:1843-1860, `h_dev_before == h_dev_after`) is untouched. completion_allowed / is_completion_request / completion_refusal / gates_completion are not in the diff. effective_step_limit was reordered but is inert when post_write_step_limit == 0 (written_step_limit() then returns step_limit), so every caller that does not name the field keeps the old behaviour byte-for-byte. The only pre-existing test whose text changed is the_effective_budget_is_stated_in_the_prompt_exactly_once, and only its three call sites gained the 5th argument; every assertion is unchanged (verified in the diff and at guard.rs:1644-1671). Under tests/ the numstat is 472 added / 0 deleted; test-attribute counts go 819 -> 830 with +5 in guard.rs and +6 in the new file and no file decreasing. The reworded note ('the first successful project write raises it to 150' -> 'once it has written, the budget in force is 35. Both numbers are re-read at every step') and the reworded StepBudget fail message ('in whichever direction the configuration says') are accurate for the shipped 43 -> 35 shape; the recorded prompts carry the old wording, and the byte delta is -1 byte per call (-9 tokens over 36 calls). The new guard test pins the 35 wording and forbids 'raises it to 150'."
  },
  {
   "id": "C6",
   "question": "Gate: cargo test --offline exit 0 with counts, fmt exit 0, zero warnings, no test removed, own build dir, disk checked, no rm -rf.",
   "pass": true,
   "evidence": "Own build dir G:/pwb-accept-target on G: (358 GiB free) after checking F: (8.2 GiB free, 100% used); one test process at a time. cargo test --offline literal exit code 0: 824 passed / 0 failed / 6 ignored, 62 test result lines, 830 listed by -- --list (exit 0), 6 by -- --list --ignored (exit 0). Grep over the whole log: 0 compiler warning lines (the only 'warning' strings are five test names), 0 error lines. cargo fmt --all --check exit 0 with 0 stdout/0 stderr bytes. No file was deleted by me; no rm -rf and no wildcard deletion was used anywhere in this review."
  }
 ],
 "defects": [
  {
   "id": "D1",
   "severity": "medium",
   "what": "The artefact's projection tables apply the post-write bound to live-completion1-iter-3, the one recording that produced no engineering write, for which the bound by construction never applies. In candidate_bounds every row with B <= 40 gives that recording the bound-cut cost (e.g. B=35 -> 36 calls / 654,384) instead of the correct 44 calls / 803,027; and bound_chosen.projected_effect_at_the_chosen_bound.bound_or_the_recorded_first_legitimate_exit also lists it as 36 calls / 654,384 / 0.4363x. This contradicts the report's own bound-alone row and its §4 note ('wrote nothing, so the post-write bound never applies: it still ends on the unwritten allowance at 44 calls'). It does not change the chosen bound and does not touch the headline claim, which is explicitly restricted to the six producing calls, but a reader summing the table would overstate the saving on that recording for every B <= 40.",
   "reproduction": "python /g/pwb-verify/prefix2.py (P(36)=654,384 and P(44)=803,027 for the iter-3 recording) and python /g/pwb-verify/writes2.py (project=[] and scratch=[] for that recording), beside src/config.rs:329-338 (`if has_written` is the only route to the bound)."
  },
  {
   "id": "D2",
   "severity": "low",
   "what": "The §2 table row for live-completion1-iter-3 gives its scratch writes as 'scratch only', but that recording contains zero extra.hoh_write_path observations of any kind (I counted 0 occurrences of the key), which is what the report's own method says the column counts. The call did copy a file to %HOH_SCRATCH_DIR% with an ordinary shell command, which the guard does not count - itself a small instance of the shell-write risk the report discloses, but not a guard-visible scratch write.",
   "reproduction": "grep -c hoh_write_path runs/completion1/iter-3/traj/developer.attempt1.json -> 0; python /g/pwb-verify/i3.py shows HOH_WRITE_FILE only in the system/user prompts and the scratch copy spelled with %HOH_SCRATCH_DIR%."
  },
  {
   "id": "D3",
   "severity": "low",
   "what": "config/hoh.yaml's steps_per_artifact comment still ends '第一次成功写入后恢复完整的 150 步' (after the first successful write, the full 150 steps are restored), which is now false: the written budget is 35. The new post_write_step_limit comment immediately below corrects it, so the file contradicts itself.",
   "reproduction": "config/hoh.yaml line 77 versus the code and the post_write_step_limit comment at lines 90-106."
  },
  {
   "id": "D4",
   "severity": "info",
   "what": "Provenance snapshot staleness, not a mechanism defect: the artefact's structured block says 'committed: false' and 'head_kind: working tree on top of b6e9364 ... uncommitted', but the repository now has commit e900262 'feat(guard): bound a call once it has produced its engineering write' on b6e9364 containing exactly these seven files. DECISIONS.md D316 says '未提交、未推送（由上层决策代理提交）', so the commit was the dispatcher's, after the report was generated. The report's claim was true of the batch; it is not true of the tree at review time.",
   "reproduction": "git log --oneline -2, git show --stat e900262, git status --porcelain (clean)."
  }
 ],
 "risks": [
  {
   "id": "R1",
   "risk": "The margin is thin: 47,693 tokens = 3.18% of the criterion on the binding recording, with no variance estimate (one provider, one model, one project shape). One call later is over by 2,443 tokens. Mitigating: the binding recording is a pre-fix round-4 call whose per-call cost is 2-3.5x that of the post-fix live calls (live calls project to 0.37-0.42x at the same 36 calls), so it is a conservative binding constraint; the prompt delta from the reworded note is -1 byte per call."
  },
  {
   "id": "R2",
   "risk": "A bound-cut artifact that is not launchable triggers the DR-18 wrap-up retry: a second Developer call (step_limit 25, written budget min(35,25)=25, at most 26 billed calls). No projection includes it; a proxy from the recorded 26-call prefixes puts the addition at roughly 0.38M-0.97M tokens on the round's Developer stage. It did not fire in any recorded iteration because hoh.artifact_valid was true throughout (including the zero-write iter-3), but a partial game.rs that breaks compilation would change that."
  },
  {
   "id": "R3",
   "risk": "The lever only works if the live model emits a counted HOH_WRITE_FILE directive write. A project changed only through the shell leaves artifact_written false, so the call keeps the 43-call unwritten allowance (44 billed) and the criterion does not move; recorded live-completion1/iter-3 shows shell-side scratch activity with zero counted writes. The base rate of shell-side project writes is unmeasured."
  },
  {
   "id": "R4",
   "risk": "The bound changes the model's instructions for every call (the [budget] note now states 35 post-write where the recordings stated 150). The projection holds the recorded call sequence fixed and cannot see the behavioural effect; the report labels this inferred."
  }
 ],
 "unverified": [
  "That a live Developer call cut at 36 calls costs the recorded prefix to call 36. Exact for calls already recorded, unknown for what the model does next.",
  "Whether the bound-cut artifact is still launchable, and therefore whether the DR-18 wrap-up retry fires.",
  "The base rate of shell-side project writes and of refused completions (the corpus contains no extra.hoh_exit_refused observation; the count is 0 by construction there).",
  "The untouched-tree baseline run (813 passed / 0 failed / 6 ignored / 819 listed): I confirmed the 819 -> 830 test-attribute delta per file and the arithmetic 819-6=813, but did not build b6e9364 in a second worktree because that would have been a second test process and a repository mutation."
 ],
 "own_figures_beside_reported": [
  {
   "figure": "criterion tokens per Developer call",
   "reported": 1500000,
   "mine": 1500000,
   "matches": true
  },
  {
   "figure": "zero-context floor for a 150-call live call",
   "reported": 2077238,
   "mine": 2077238,
   "matches": true
  },
  {
   "figure": "off-by-one: unwritten budget 43 -> billed calls in completion1/iter-3",
   "reported": 44,
   "mine": 44,
   "matches": true
  },
  {
   "figure": "binding prefix(36) round4-iter-3",
   "reported": 1452307,
   "mine": 1452307,
   "matches": true
  },
  {
   "figure": "binding prefix(37) round4-iter-3",
   "reported": 1502443,
   "mine": 1502443,
   "matches": true
  },
  {
   "figure": "headroom on the binding recording",
   "reported": 47693,
   "mine": 47693,
   "matches": true
  },
  {
   "figure": "guard unit tests before -> after",
   "reported": "29 -> 34",
   "mine": "29 -> 34",
   "matches": true
  },
  {
   "figure": "new integration tests",
   "reported": 6,
   "mine": 6,
   "matches": true
  },
  {
   "figure": "gate passed/failed/ignored/listed",
   "reported": "824/0/6/830",
   "mine": "824/0/6/830",
   "matches": true
  },
  {
   "figure": "baseline listed -> current listed",
   "reported": "819 -> 830",
   "mine": "819 -> 830",
   "matches": true
  },
  {
   "figure": "the combined-table live-completion1-iter-3 row",
   "reported": "36 calls / 654384",
   "mine": "44 calls / 803027",
   "matches": false
  }
 ]
}
```

# ACCEPTANCE-POST-WRITE-BOUND - the post-write call bound, independently verified

This is a fresh independent acceptance. I inherited no conclusion from the implementer or the
dispatcher; every number below was re-derived from the code, the configuration and the recordings.
**No round was run, no model call was made, no engine was started, no network was used.** I did not
modify `src/**`, `tests/**`, `evidence/**`, the registry, the battery, the liveness step,
`.gitattributes` or any frozen document; I wrote nothing under `runs/**`, committed nothing, staged
nothing, pushed nothing, and fixed nothing. Helper scripts live outside the repository at
`G:/pwb-verify/` and every one of them landed through a file write (never multi-line Python on a
shell command line). No `rm -rf` and no wildcard deletion was used. The build used its own directory
`G:/pwb-accept-target` on `G:` (358 GiB free) after checking `F:` (8.2 GiB free, 100 % full), with one
test process at a time.

## 1. What I checked, and what I found

| # | item | result | key evidence |
|---|---|---|---|
| 1 | mechanism, off-by-one, production wiring | **pass** | `compact.rs:302` increments per model call; `config.rs:329-353` computes `min(35,150)=35` only when `has_written`; `guard.rs:868-881` enforces `steps > budget`; `mini.rs:133` wires `inv.limits.post_write_step_limit` in production |
| 2 | compatibility: unreachable before a write, arithmetic at the edges | **pass** | the bound is read only through `artifact_written()`; P(36)=1,452,307 under, P(37)=1,502,443 over by 2,443; lower edge 33 is flat-reading-only, as stated |
| 3 | projections re-derived | **pass**, one table error | every prefix, write call and declared finish reproduces exactly; the combined table's live-i3 row is wrong (D1); the `min(bound, exit)` combination is legitimate, not double counting |
| 4 | uncovered wrap-up cost and the directive-write dependency | **pass** | retry verified at `run_loop.rs:1735` with `min(25,30)`; adds ~0.38M-0.97M if it fires and did not fire in any recorded iteration; shell writes never set `artifact_written` |
| 5 | no weakening | **pass** | only 3 production files + 1 config + the new test file; 472 added / 0 deleted under `tests/`; only one existing test changed and only its call sites |
| 6 | gate | **pass** | `cargo test --offline` exit **0**: 824 / 0 / 6 / 830; `cargo fmt --all --check` exit 0; 0 warnings; 0 errors |

## 2. Item 1 - the mechanism and the bound's semantics

**A step is a model call.** `src/harness/compact.rs:302`, inside `CountingModel::query`:

```rust
self.progress.steps.increment();
self.inner.query(messages, kwargs).await
```

and `src/harness/mini.rs:126-133` hands that same counter to the guard and wires the bound:

```rust
.sharing_steps(steps)
// Round-6 cost repair (the post-write call bound): ...
.with_post_write_step_limit(inv.limits.post_write_step_limit);
```

**Where the budget is computed** (`src/config.rs:329-353`):

```rust
pub fn effective_step_limit(&self, has_written: bool) -> u64 {
    if self.steps_per_artifact == 0 { return self.step_limit; }
    if has_written { return self.written_step_limit(); }
    let per_artifact = (self.step_limit / self.steps_per_artifact).max(1);
    (self.wrap_up_steps + per_artifact).max(self.wrap_up_steps)
}
pub fn written_step_limit(&self) -> u64 {
    if self.post_write_step_limit == 0 { return self.step_limit; }
    self.post_write_step_limit.min(self.step_limit)
}
```

**Where it is enforced** (`src/harness/guard.rs:868-881`, the first statement of `execute`):

```rust
let budget = self.effective_step_budget().min(self.step_limit);
let steps = self.steps();
if steps > budget { Some(FailFast::StepBudget { steps, budget }) } else { None }
```

with `effective_step_budget() = self.limits().effective_step_limit(self.artifact_written())`
(`guard.rs:809-811`).

**The off-by-one.** `steps > budget` with the counter incremented before the request is forwarded
means calls `1..=B` act and call `B+1` is billed and then refused. I did not take this on the
report's word: the recorded unwritten round `runs/completion1/iter-3/traj/developer.attempt1.json`
has `hoh.usage.calls = 44`, 44 response-bearing messages, `exit_status = StepBudgetExceeded` and
803,027 tokens against the unwritten budget of 43 - which is exactly `B+1` for `B = 43`.

**The value reaches the enforcement point in production.** The chain is
`config/hoh.yaml agent.post_write_step_limit: 35` -> `load_config`'s `take_section` -> `HohConfig.agent`
-> `run_loop.rs:1702 limits: cfg.agent.clone()` -> `mini.rs:133` -> the guard's
`post_write_step_limit` field -> `limits()` -> `effective_step_budget()` -> `step_budget_exceeded()`.
The production-path tests drive the real `MiniHarness::invoke` against a `127.0.0.1` fake chat
endpoint, so they test the passing-on, not just the arithmetic; and the shipped-number test asserts
`effective_step_limit(true) == 35` from `load_config(&[])`, i.e. from the file. I accept this as
the answer to the "the value exists but the harness never passes it" defect class.

## 3. Item 2 - the compatibility argument

**The bound is genuinely unreachable before a write.** The only enforcement read is
`effective_step_budget()`, and `artifact_written` is set true only by a successful directive write to
a non-excluded path (`guard.rs:1035-1048`; `ArtifactKind::ProjectFile::counts` is
`!is_excluded_path(path)`). The guard is constructed inside every `MiniHarness::invoke`, so the flag
starts false for each call. A call that has not written therefore always sees
`25 + max(150/8,1) = 43` and can never see 35. A call that is cut *after* its write is cut after the
artifact exists - the constraint the task names is satisfied structurally, for any value of the key.

**The arithmetic at the window's edges.** I prefix-summed each recording's own
`extra.response.usage.total_tokens` over every response-bearing message (not only `role ==
"assistant"`: `round4-iter-3` carries 8 of its 102 responses on `user` messages, and including them
made my per-call sum equal `hoh.usage.total_tokens` exactly for all seven recordings -
5,223,211 / 13,091,431 / 2,626,195 / 3,651,120 / 3,527,566 / 3,939,027 / 803,027). For the binding
recording, `round4-iter-3`:

| calls | my prefix | ratio | verdict |
|---|---|---|---|
| 35 | 1,403,409 | 0.9356x | under |
| **36** | **1,452,307** | **0.9682x** | **under by 47,693 (3.18 %)** |
| **37** | **1,502,443** | **1.0016x** | **over by 2,443** |

So a bound of 35 bills 36 calls and passes; 36 bills 37 and misses by 2,443. The lower edge: first
project writes are 7 / 33 / 6 / 6 (corpus) and 8 / 13 (live), all `<= 33`, so a *flat* reading needs
`B >= 33`; with the actual post-write semantics any `B` works. The window 33-35, with that
qualification, is correct.

**What the thin margin implies.** 3.18 % is not a margin, it is one recording's arithmetic with no
variance behind it, and one call later is over. The saving grace is that the binding recording is a
pre-fix round-4 call whose per-call context is 2-3.5x that of the post-fix live calls, which project
to 0.37-0.42x at the same 36 calls - so 35 is a conservative reading, not an optimistic one. It is
defensible as "the largest bound the recordings support" and not as "a bound with proven headroom",
which is exactly how the report states it.

## 4. Item 3 - the projections

I re-derived every figure in the report's tables from the recordings. All prefix sums, write calls,
project/scratch splits and declared finishes reproduce the report exactly; the cross-check the report
offers also reproduces (prompt tokens over calls 1..24 of `round4-iter-1` = 579,603 =
2,544,563 - 1,964,960).

| recording | first write | declared finish | B=35 cost (36 calls) | ratio | under? |
|---|---|---|---|---|---|
| round4-iter-1 | 7 | 25 | 1,127,441 | 0.7516x | yes |
| round4-iter-2 | 33 | 58 | 1,196,549 | 0.7977x | yes |
| round4-iter-3 | 6 | 30 | 1,452,307 | 0.9682x | yes (binding) |
| livecost1-iter-1 | 6 | none | 558,945 | 0.3726x | yes |
| live-completion1-iter-1 | 8 | none | 579,120 | 0.3861x | yes |
| live-completion1-iter-2 | 13 | none | 633,893 | 0.4226x | yes |
| live-completion1-iter-3 | none | none | 44 calls / 803,027 | 0.5354x | n/a - no write |

**"Every recorded producing Developer call lands under the criterion" is true** at the chosen bound,
holding each recorded call sequence fixed: all six producing calls are under, and the margin is
3.18 % at its tightest.

**Is the artefact overstating it?** The headline is not: it is explicitly restricted to the six
producing calls, and it is labelled a projection. The `min(bound, recorded first legitimate exit)`
combination is **legitimate arithmetic, not double counting**: the two are independent stopping rules
and the call ends at whichever fires first, and the calls before the earlier of the two are unchanged
because the bound cannot bite before call 36 in the unwritten case and the exit already follows the
write in the producing case. The overstatement is confined to two tables, and is recorded as D1:
`live-completion1-iter-3` never wrote, so the post-write bound can never apply to it, yet the candidate
table (all rows `B <= 40`) and the combined-effect table give it the bound-cut value. The report's own
bound-alone row and §4 note get it right (44 calls / 803,027), so the tables contradict the prose.

## 5. Item 4 - what it does not cover

**The wrap-up retry is real and is not in any projection.** `src/runtime/invoke.rs:268-276` treats
`StepBudgetExceeded` as a limit; `run_loop.rs:1708` sets `developer_limits`, `:1718` reads the
adapter's `developer_artifact_valid`, and `:1735` fires a second Developer call when
`developer_limits && !developer_artifact_valid`, with `wrap_base.limits.step_limit =
cfg.agent.wrap_up_steps.min(WRAP_UP_RETRY_MAX_STEPS) = min(25,30) = 25`. The retry inherits
`post_write_step_limit = 35`, so its written budget is `min(35,25) = 25` - at most 26 billed calls.
Using the recorded 26-call prefixes as a proxy (382k-971k depending on context) the retry adds
roughly **0.38M-0.97M tokens** to the round's Developer stage. It did **not** fire in any recorded
iteration: there is no `developer.attempt2.json` anywhere under `runs/completion1/iter-*/traj/`, and
`hoh.artifact_valid` is `true` in all seven recordings - including the zero-write `iter-3`, whose
scaffold was already launchable. So the risk is conditional and did not materialise in the recorded
rounds, which is a stronger statement than the report makes.

**The directive-write dependency is real.** `artifact_written` is set only in `execute_write` for a
counted path; a project changed through the shell leaves it false, the budget stays 43, the call bills
44 and the criterion does not move. The recorded corpus does use the directive (first writes at
7/33/6/6 and 8/13 all carry `extra.hoh_write_path`), but that is the same corpus the bound was fitted
to, and the base rate of shell-side project writes is unmeasured. `live-completion1/iter-3` is a
recorded instance of shell-side scratch activity with zero counted writes, which is a small live
sighting of the shape.

## 6. Item 5 - no weakening

`git diff b6e9364 e900262` touches seven files and nothing else: `src/config.rs`,
`src/harness/guard.rs`, `src/harness/mini.rs`, `config/hoh.yaml`, `tests/post_write_bound.rs`,
`DECISIONS.md`, `.spec/bevy/POST-WRITE-BOUND-REPORT.md`. `src/runtime/**` is untouched, so the
round's `NoEngineeringWrite` gate (`run_loop.rs:1843-1860`, `h_dev_before == h_dev_after`) is
unchanged and **a round that writes nothing still fails**. The write guarantee
(`completion_allowed`, `is_completion_request`, `completion_refusal`, `gates_completion`) does not
appear in the diff at all. `effective_step_limit` was reordered so that `steps_per_artifact == 0`
still returns `step_limit` first, and `written_step_limit()` returns `step_limit` when
`post_write_step_limit == 0` - so every caller that does not name the field keeps the pre-repair
behaviour exactly. The unwritten allowance is `25 + max(150/8,1) = 43`, unchanged, and pinned by the
new guard test `the_unwritten_guard_is_untouched_by_the_post_write_bound` (refused at step 44, message
contains `live step budget is 43`) and by the MiniHarness control (6 calls at unwritten 5 while the
bound is 3).

**No test was removed or weakened.** `tests/` numstat is 472 added / 0 deleted. Test attributes go
819 -> 830: `src/harness/guard.rs` 29 -> 34 and the new `tests/post_write_bound.rs` 0 -> 6, every
other file identical. The only pre-existing test whose text changed is
`the_effective_budget_is_stated_in_the_prompt_exactly_once`, and only its three call sites gained the
fifth argument; its assertions are unchanged. The 17 deleted lines in `guard.rs` are one module-doc
sentence, the two reworded messages, the reworded note branch, the refactor of `limits()`, and the
three test call sites - no assertion.

**The reworded note and message are accurate.** The note now says the unwritten budget is 43 and
"once it has written, the budget in force is 35. Both numbers are re-read at every step"; the fail
message says the budget "changes ... in whichever direction the configuration says". Before this
batch the note promised "the first successful project write raises it to 150", which would have been
false in the direction that matters once 35 < 43. One inconsistency remains, recorded as D3: the older
`steps_per_artifact` comment in `config/hoh.yaml` still says a write restores the full 150.

## 7. Item 6 - the gate

| check | literal exit code | result | report |
|---|---|---|---|
| `cargo test --offline` | **0** | **824 passed / 0 failed / 6 ignored**, 62 `test result:` lines, 0 compiler warnings, 0 error lines | 824 / 0 / 6, matches |
| `cargo test --offline -- --list` | **0** | **830** test lines | 830, matches |
| `cargo test --offline -- --list --ignored` | **0** | **6** test lines | 6, matches |
| `cargo fmt --all --check` | **0** | 0 stdout bytes, 0 stderr bytes | 0, matches |

Build directory `G:/pwb-accept-target`, one test process at a time, disk checked first. The only
"warning" strings in the log are five test names; there are no compiler warnings. The delta from the
report's baseline is confirmed at the source level (819 -> 830 attributes, +5 guard, +6 new file, no
file decreasing), which also reproduces the arithmetic 819 - 6 = 813 passed.

## 8. Defects

| id | severity | what | reproduction |
|---|---|---|---|
| D1 | medium | the candidate table (`B <= 40`) and the combined-effect table apply the post-write bound to `live-completion1-iter-3`, which never wrote, giving 36 calls / 654,384 at `B = 35` instead of 44 calls / 803,027 - contradicting the report's own bound-alone row and §4 note; the bound choice and the headline (producing-only) claim are unaffected | `python /g/pwb-verify/prefix2.py`, `python /g/pwb-verify/writes2.py`; `src/config.rs:329-338` |
| D2 | low | the §2 table gives `live-completion1-iter-3` "scratch only" for scratch writes, but the recording has zero `extra.hoh_write_path` observations; its scratch copy was a shell command under `%HOH_SCRATCH_DIR%`, which the guard does not count | `grep -c hoh_write_path runs/completion1/iter-3/traj/developer.attempt1.json` -> 0 |
| D3 | low | `config/hoh.yaml`'s `steps_per_artifact` comment still promises "第一次成功写入后恢复完整的 150 步" while the written budget is now 35 | `config/hoh.yaml` line 77 vs the new comment at lines 90-106 |
| D4 | info | the structured block says `committed: false` / "uncommitted", but HEAD is e900262 containing exactly these files; D316 says the dispatcher commits, so this is snapshot staleness, not a batch violation | `git log --oneline -2`, `git show --stat e900262`, `git status --porcelain` |

## 9. Risks

* **R1 - thin margin.** 47,693 tokens = 3.18 %, no variance estimate, one call later over by 2,443.
  Mitigated by the binding recording being a pre-fix call 2-3.5x more expensive per call than the
  post-fix live calls, and by the reworded note changing the prompt by -1 byte per call.
* **R2 - the uncovered wrap-up retry.** A bound-cut unlaunchable artifact fires a second Developer
  call (<= 26 billed calls, ~0.38M-0.97M tokens by the recorded 26-call prefixes). It did not fire in
  the recorded rounds, but that is a different call length.
* **R3 - efficacy depends on a counted directive write.** A shell-only project write leaves the bound
  disengaged and the call at 43/44; the base rate is unmeasured.
* **R4 - the instruction change is behavioural and unmeasured.** The projection holds the recorded
  sequence fixed and cannot see what the model does when told the post-write budget is 35.

## 10. What I could not establish

That a live call cut at 36 calls costs the recorded prefix (exact for the recorded calls, unknown for
what the model does next); whether a bound-cut artifact stays launchable and therefore whether the
retry fires; the base rate of shell-side project writes and of refused completions (the corpus has no
`extra.hoh_exit_refused` observation at all); and the untouched-tree baseline run - I confirmed
819 -> 830 test attributes per file and the arithmetic 819 - 6 = 813, but did not build `b6e9364`,
because that would have been a second test process and a repository mutation.

## 11. Conclusion

**pass.** The mechanism is quoted from the code and wired in production, not only in tests; the
off-by-one is confirmed from the code and from a recording; the binding arithmetic is exact and the
margin is honestly thin; the bound is structurally unreachable before a write; the write guarantee,
the unwritten allowance and the round's zero-write failure are unchanged and no test was removed or
weakened; and the gate reproduces at 824 / 0 / 6 / 830 with exit 0, fmt exit 0 and zero warnings. Two
errors inside the artefact's own projection tables (D1, D2) and one stale comment (D3) are recorded
above; none of them touches the binding arithmetic or the claim as stated, which is restricted to the
six recorded producing calls - and that claim is verified true.
