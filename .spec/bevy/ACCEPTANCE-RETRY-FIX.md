
# ACCEPTANCE-RETRY-FIX — independent acceptance of the Developer format-error retry fix

**Who.** This is a fresh, independent acceptance pass. It inherited no conclusion from the
implementer or the dispatcher. Every number below was re-derived from
`evidence/cost/*.developer.attempt1.json` and from the code, and the gate was re-run in its own build
directory. **No round, no model call, no engine, no network.** Nothing was fixed, committed, staged or
pushed; no `rm -rf`, no wildcard, no `git checkout --`; helper scripts live outside the repository at
`F:/retry-acc/`.

**What was reviewed.** The batch commit `9b74379` on `bevy-core` (working tree clean at review time;
the report's `head_at_start 9d3f488` is its pre-commit parent) and `.spec/bevy/RETRY-FIX-REPORT.md`.
The motivating measurement is lever 4 of `.spec/bevy/SPIKE-COST-LEVERS.md`.

**Verdict: `pass`.** The diagnosis holds — the rejected shape is real, it is exactly the shape the
prompts invited, the marker really can only exit a call as the first line of a command's output, and
no role ever ran it. The change reaches every delivered prompt on the single path the batch claims,
and **no validation was weakened**: the parser, the format-error template, the consecutive-error limit,
the guard and every fail-fast path are unchanged, the vendored mini crate is untouched, and no test was
removed or relaxed. The five defects recorded below are about the accuracy of the report's prose and
one of its ratios, not about what the fix does. The gate is green with exactly the reported counts.

The structured verdict is the first JSON block, below. It was produced by a serialiser and parsed back
out of this file (`json.loads` over the fenced block, `criteria` 7, `defects` 5).

```json
{
  "schema": "hof-rs / independent acceptance of the Developer format-error retry-fix batch",
  "artifact_under_review": ".spec/bevy/RETRY-FIX-REPORT.md",
  "reviewed_commit": "9b74379 (working tree clean at review time; report's head_at_start 9d3f488 is its pre-commit parent)",
  "review_kind": "independent, offline, re-derived from evidence/cost/*.json and src/**; no round, no model call, no engine, no network",
  "verdict": "pass",
  "criteria": [
    {
      "id": "C1-failing-shape",
      "pass": true,
      "claim": "all 38 rejected turns share one shape (prose, no tool calls, normal finish reason) and the other shapes are absent",
      "own_finding": "Confirmed 38 rejected (FormatError) turns: 20 / 10 / 8 / 0 over round4-iter-1/2/3/livecost1-iter-1. Every one has finish_reason='stop', content = a list of one or more {type:text} parts (1431-2969 chars), no fenced block, no embedded \"command\" JSON. Across ALL 446 recorded responses the finish_reason census is exactly {tool_calls: 408, stop: 38}; the 38 'stop' responses are exactly the 38 rejected turns. No `length`, no empty tool_calls array, no unparsable arguments, no unknown tool name, no missing `command`; `bash` is the only tool (59/122/108/172 calls).",
      "reported_finding": "distinct_shapes_found=1, 38 instances, 29/9 marker split, shapes_left_unfixed=[]",
      "divergence": "report collapses into one shape what is two: marker-bearing (29) and marker-less (9). The two differ only in the marker's presence, so 'one shape' is defensible; 'distinct_shapes_found: 1' is inexact. Also `message.tool_calls` is the ABSENT key, not null/none.",
      "evidence": "F:/retry-acc/census2.json, F:/retry-acc/absence.py output"
    },
    {
      "id": "C2-root-cause",
      "pass": true,
      "claim": "the marker only exits as the first line of a command's output, and the roles quoted it in prose while never running it",
      "own_finding": "Confirmed in the dependency source: LocalEnvironment::check_finished (mini .../environments/local.rs:118-128) trims leading whitespace, takes the text before the first newline, and returns FlowInterrupt::submitted only when that first line equals the marker AND returncode==0. LlmConnectorModel::parse_actions (models/mod.rs:139-153) returns an empty-tool-call FormatError for a reply with no tool calls, and src/harness/mini.rs:80 builds the model with ApiMode::ToolCalls. Attestation: 29/38 rejected bodies quote the marker verbatim, and 0 of the 59/122/108/172 recorded bash calls (nor any recorded `actions` entry) contains the marker. No role ever ran it.",
      "reported_finding": "same mechanism and the same 29/38 and 0/4 counts",
      "divergence": "none material",
      "evidence": "F:/retry-acc/census2.json; local.rs:118-128; models/mod.rs:139-153; mini.rs:80"
    },
    {
      "id": "C3-change-coverage-and-validation",
      "pass": true,
      "claim": "the substitution reaches every delivered prompt, no validation was weakened, the mini crate was not modified",
      "own_finding": "All five delivered role system prompts go through render_prompt_with_budget_and_shell -> render_prompt_for_shell (run_loop.rs:1448, 1498, 1683, 1741, 2001, 2295, 2345); that function is the only substitution site and now replaces {{completion_protocol}} (invoke.rs:162-165). src/prompts/{developer,planner,tester}.md are the only files carrying the placeholder; it is consumed by every render. Nothing else changed: parse_toolcall_actions, the format-error template, max_consecutive_format_errors (mini's, still passed through from inv.limits), the guard and the fail-fast paths are byte-identical to 9d3f488; the new section carries no {{HOH_*}} token, so its position in the chain is not load-bearing. F:/RustProjects/mini-swe-agent-rust-mini is a separate git repository with a clean working tree at c39b0c7: no vendored file was touched. A genuinely malformed reply is still rejected: no code path accepts a no-tool-call reply, and the new text adds no acceptance.",
      "reported_finding": "files list and the 'nothing was weakened' claim",
      "divergence": "none; the claim checks out from the code, not merely from the report",
      "evidence": "git show 9b74379 -- src/; grep of render_prompt call sites; mini crate git status"
    },
    {
      "id": "C4-tests",
      "pass": true,
      "claim": "two new tests, red with literal exit 101 then green 0, exercising a real environment, and failing against the old prompts",
      "own_finding": "Ran the suite myself: tests/prompt_shell_contract.rs is in the 802-passed set and prompts no failures, exit 0. The green path executes the lifted command through the real mini LocalEnvironment::execute (imports mini_swe_agent::{Action, Environment, LocalEnvironment}) and asserts AgentError::Interrupt with InterruptKind::Submitted from check_finished - the same type MiniHarness constructs (mini.rs:98). Not a stub. The red state is not reproducible from the current tree, but the claimed assertions are exactly the ones at tests/prompt_shell_contract.rs:464 (completion_command panic when no `echo ...MARKER` candidate exists) and :484 ('at least one tool call'); against the pre-change prompts exported from 9d3f488 none of the three contains 'at least one tool call' and none contains any fenced or inline echo command carrying the marker, so both tests would have failed for the stated reason, and the existing only_a_first_line_completion_protocol_ends_a_role_call plus its 'echo submit' control are untouched.",
      "reported_finding": "red 101 with the two named failures; green 0 with 7 passed",
      "divergence": "none found; the red run itself is historical and cannot be re-observed from a tree that already contains the prompts - that is a property of any prompt fix, not a defect",
      "evidence": "F:/retry-acc/red_state.py; git show 9d3f488:src/prompts/*.md; tests/prompt_shell_contract.rs"
    },
    {
      "id": "C5-measurement",
      "pass": true,
      "claim": "before-figures re-derived; after labelled projected; the 'rejected turn is not saved, only the cascade' nuance; the large unmeasured term",
      "own_finding": "Re-derived from the recordings by summing the usage block on every message carrying extra.response.usage - which is what src/runtime/usage.rs extract_usage counts, and which includes the FormatError messages. Parsed/rejected split 49+20=69, 115+10=125, 94+8=102, 150+0=150, exactly the recorded hoh.usage.calls; totals match hoh.usage.prompt_tokens to the token (2,544,563 / 12,765,478 / 5,137,090 / 3,537,843). Retry turns 20/10/8/0, their own prompt tokens 876,566 / 1,486,702 / 416,910, shares 34.45% / 11.65% / 8.12% / 0 - all as reported. Retry call numbers reproduce exactly. Marker-quoting 17/7/5 (29). Dropping the rejected messages from the total gives 1,667,997 / 11,278,776 / 4,720,180 / 3,537,843, which are exactly the report's 'floor_if_the_rejected_calls_were_simply_not_sent' - an independent cross-check that the report's own arithmetic is self-consistent. The nuance is right: the rejected assistant message is NOT saved (the trajectory at each rejection holds only the FormatError user message, whose prose lives in extra.response), so the rejected turn's own tokens stay spent and become the legal completion turn; only the FormatError history message and its re-sends disappear. The after column is labelled projected, not measured - correct. Tail re-derived: calls 25..69 = 1,964,960 (876,566 + 1,088,394 successful); 58..125 = 9,812,332 (1,486,702 + 8,325,630); 30..102 = 4,059,147 (416,910 + 3,642,237) - all three reproduce the report exactly.",
      "reported_finding": "the same before figures and the same tail figures",
      "divergence": "the report calls the tail 'unmeasured' / 'cannot quantify offline'. It is arithmetic over recorded usage and reproduces to the token; what is genuinely unknowable is not the number but whether a live role ends there. The distinction matters because the report tells the reader the number needs a live call, when the number is already available from the corpus.",
      "evidence": "F:/retry-acc/census2.json, F:/retry-acc/tails.json"
    },
    {
      "id": "C6-gate",
      "pass": true,
      "claim": "cargo test --offline exit 0 with the stated counts, fmt exit 0, zero warnings, nothing removed",
      "own_finding": "Own build directory D:/retry-acc-target (D: had 72G free; F: only 9.1G, checked first), one test process at a time, no rm -rf and no wildcard used. cargo test --offline: literal exit code 0, 802 passed / 0 failed / 6 ignored / 808 per-test lines / 60 'test result' lines / 0 compiler warning lines / 0 error lines. cargo test --offline -- --list: exit 0, 808 test lines. cargo test --offline -- --list --ignored: exit 0, 6 test lines. cargo fmt --all --check: exit 0, 0 bytes on stdout and stderr. Against the stated baseline 800/0/6/806 the delta is exactly the two new tests; nothing was removed.",
      "reported_finding": "identical counts and literal exit codes",
      "divergence": "none",
      "evidence": "F:/retry-acc/gate.out, F:/retry-acc/gate.err, F:/retry-acc/list.out, F:/retry-acc/listign.out, F:/retry-acc/fmt.out"
    },
    {
      "id": "C7-early-end-risk",
      "pass": true,
      "claim": "judge whether the change can end Developer calls earlier with weaker artifacts",
      "own_finding": "Yes, and the report names it correctly. The old prompt already told the role to decide when it was finished, and the recordings show it deciding at call 25/58/30 (of 69/125/102) while the prose says so; the old text gave it no executable way to act on that decision, so the reply was rejected and the working sequence continued. Making the decision executable removes that accidental brake. The harness's only artifact check for the Developer, adapter::developer_artifact_valid -> developer_artifact_defects (adapter/bevy/project.rs:469-508), verifies the crate name, the manifest, the lockfile and the frozen contract paths - it says nothing about whether the iteration's plan was implemented. exit_status 'Submitted' is not a failure status (runtime/write_failure.rs:44-54), and the Developer wrap-up retry only fires on a limits-exceeded exit with an invalid artifact (run_loop.rs:1735). The early-end protection is therefore the launchable gate and the battery, plus the Tester, not the Developer's exit path. A live round must check: (a) call count and prompt tokens versus the recorded 69/125/102/150 baselines; (b) exit_status 'Submitted' occurring at the first self-declared finish; (c) artifact_valid at that moment; (d) whether the battery/launch gate pass on the first pass rather than needing the one targeted repair (run_loop.rs:1970-2079) - that retry is the mechanism by which an early end costs a second Developer call, and it is where a weaker artifact would surface.",
      "reported_finding": "the report states the same risk in its single_most_important_thing",
      "divergence": "the report says the fields to read are exit_status, the artifact write and artifact_valid; that is right but incomplete - the decisive observable is the first-pass launchable gate and whether a repair retry was consumed, because artifact_valid cannot detect a valid-but-unfinished artifact.",
      "evidence": "run_loop.rs:1707-1771, 1970-2079; adapter/bevy/project.rs:469-508; runtime/write_failure.rs:44-54"
    }
  ],
  "defects": [
    {
      "id": "D1",
      "severity": "low",
      "what": "The report's measurement method says 'a model call is one such message (assistant = parsed, user/FormatError = rejected)' and then says the reconstruction reproduces hoh.usage exactly. The 69/125/102/150 counts and the 2,544,563 / 12,765,478 / 5,137,090 / 3,537,843 totals reproduce only because the FormatError messages are included - extract_usage (src/runtime/usage.rs:80-95) counts every message with extra.response, rejected ones too. The sentence invites the reader to attribute the recorded total to the parsed calls alone, under which reading the retry share would look like 52.5% / 13.2% / 8.8% instead of 34.4% / 11.6% / 8.1%.",
      "reproduction": "sum extra.response.usage.prompt_tokens over assistant messages only: 1,667,997 / 11,278,776 / 4,720,180 / 3,537,843 - which equals the report's own floor figures, not the recorded totals. Over all messages that carry a response: the recorded totals."
    },
    {
      "id": "D2",
      "severity": "low",
      "what": "The report calls the post-change column 'projected' (correct) but calls the 1,964,960 / 9,812,332 / 4,059,147 tail 'the largest unmeasured term' and 'a direction I cannot quantify offline'. The tail is measured from the recordings and reproduces exactly; only its behavioural realisation is unmeasured, and a live call is needed to confirm it, not to compute it.",
      "reproduction": "sum usage.prompt_tokens over calls whose call number is >= the first rejected call: reconstructs the three figures to the token (F:/retry-acc/tails.json)."
    },
    {
      "id": "D3",
      "severity": "informational",
      "what": "Wording: the rejected responses' tool_calls field is the ABSENT key, not an explicit null ('tool_calls == null' / 'tool_calls: null' in the JSON block and the table). node: the census prints the key as '<ABSENT_KEY>' in all 38 cases. Same conclusion (no tool calls), imprecise description.",
      "reproduction": "shape_report/absence census: repr of message.tool_calls over the 38 FormatError responses is '<ABSENT_KEY>' 38 times."
    },
    {
      "id": "D4",
      "severity": "informational",
      "what": "The report's first block says distinct_shapes_found: 1 while its own table admits the 29/9 marker split. There are two content variants (marker / no marker) and the fix addresses both, so the verdict is unaffected; the count is not literally true.",
      "reproduction": "census2 shapes: ('stop','absent',('text',),'marker','no-fence','no-json-command') x29 and the same tuple with 'no-marker' x9."
    },
    {
      "id": "D5",
      "severity": "low",
      "what": "The cascade figures (889,649 / 1,494,510 / 428,655) are introduced as 'projected at each recording's own tokens-per-wire-byte ratio'. I could not reproduce their wire-byte definition: my (role, content, tool_calls, tool_call_id) compact-JSON ratio gives 0.202727 / 0.173973 / 0.210370 / 0.264771 against the report's stated 0.259864 / 0.256903 / 0.262988 / 0.338006. The cascade figure is a modelled quantity either way and its order of magnitude is consistent with the measured retry-turn byte share, but the exact number is not independently checkable from the report's stated method.",
      "reproduction": "per_byte = hoh.prompt_tokens / sum of compact (role, content, tool_calls, tool_call_id) JSON lengths over all messages."
    }
  ],
  "risks": [
    "Unmeasured behavioural half: no live round was run, so nothing here shows the role now executes `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` instead of writing it. The whole criterion, 2.6x to under 1.5M, depends on that unverified step. The recorded model also had to make the same call 20/10/8 times before; whether one prompt section changes that is a live question.",
    "Early end with a weaker artifact (see C7): a 'Submitted' exit is not a failure and developer_artifact_valid only checks the frozen scaffold; the first-pass launchable gate and the one targeted repair are the observables that would show it.",
    "The tail figure is an upper bound, not an expected saving: it holds the recorded call sequence fixed and deletes everything after the first self-declared finish, but part of that tail is ordinary project work (builds, tests, writes) that a live role would still have to do somewhere, and an early end can trigger the one repair retry (a further Developer call) if the gate fails. The report is conservative in the correct direction, but the number a human acts on is a ceiling.",
    "The projections assume the rejected shape disappears entirely. Nothing constrains a future model from producing a no-marker prose reply or another shape; the positive 'at least one tool call' sentence is an instruction, and the format error remains the only thing that enforces it.",
    "Only Developer trajectories exist in the corpus, so the Planner/Tester halves of the same change have no recorded evidence behind them (the report says so)."
  ],
  "unverified": [
    "That a live Developer call now issues the command at the moment it believes it is finished - no round and no model call were run, by instruction.",
    "The historical red run: the current tree already contains the fixed prompts, so exit code 101 and the two panic texts could only be checked against the pre-change prompts re-derived from 9d3f488 (they fail the assertions there), not re-observed.",
    "The exact wire-byte model behind the cascade figures (D5); the report's stated tokens-per-wire-byte ratios do not follow from the message schema I can see.",
    "The source of the extra 8-byte/byte_count delta in my byte-length check (extract_usage reproduces the prompt totals, so the readings are right; a minor encoding/serialisation detail differs)."
  ],
  "what_i_did": [
    "read .spec/bevy/RETRY-FIX-REPORT.md, .spec/bevy/SPIKE-COST-LEVERS.md (lever 4), all four evidence/cost/*.developer.attempt1.json, src/prompts/**, src/runtime/invoke.rs, src/harness/mini.rs, src/harness/compact.rs, src/runtime/usage.rs, src/runtime/write_failure.rs, src/runtime/run_loop.rs and the mini crate's local.rs / models/mod.rs / llm_connector.rs",
    "re-derived the call census, the shape census, the retry counts and tokens, the per-call wire-byte/token ratios and the tail sums with scripts in F:/retry-acc/ (outside the repository)",
    "ran cargo test --offline, both --list forms and cargo fmt --all --check in D:/retry-acc-target after checking free disk",
    "did not run a round, a model call, an engine or any network request; modified nothing under evidence/**, runs/**, config/**, the registry, the battery, the liveness step, .gitattributes or any frozen document; committed, staged and pushed nothing; used no rm -rf, no wildcard and no git checkout --; wrote only .spec/bevy/ACCEPTANCE-RETRY-FIX.md in the repository"
  ]
}
```

## 1. Per-item verification, my counts beside the report's

Call numbers are 1-based over all recorded model calls (a call is any message carrying
`extra.response.usage`, which is what `src/runtime/usage.rs::extract_usage` counts, rejected turns
included). "Gen" is mine; "Rep" is the report's.

| # | item | report | my re-derivation | agree |
|---|---|---|---|---|
| 1 | rejected (FormatError) turns | 20 / 10 / 8 / 0 = **38** | 20 / 10 / 8 / 0 = **38** | yes |
| 1 | shape | `stop` + no tool calls + prose 1431–2969 chars; fenced blocks and embedded JSON **0/38** | `stop` 38/38; no `tool_calls` key 38/38; content a list of `{type:text}`; fences 0/38; `"command"` JSON 0/38; lengths 1431–2969 | yes |
| 1 | other shapes absent | no `length`, no empty array, no bad args, no unknown tool, no missing `command` | across **all 446** responses: `finish_reason` is `tool_calls` 408 / `stop` 38, and the 38 `stop`s are exactly the 38 rejections; `bash` is the only tool (59/122/108/172) | yes |
| 1 | marker-quoting | 29/38 (17/7/5) and 9 without | 29 (17/7/5) and 9 (3/3/3) | yes |
| 1 | shapes left unfixed | `[]` | `[]` — both variants (marker, no marker) are addressed by the two halves of the fix | yes |
| 2 | marker exits only as first line | `local.rs:118-128` | `check_finished` trims leading whitespace, takes text before the first `\n`, requires equality **and** `returncode == 0` | yes |
| 2 | no-tool-call reply is a format error under `ApiMode::ToolCalls` | `models/mod.rs:139-153` via `harness/mini.rs` | `parse_toolcall_actions` returns that `FormatError`; `mini.rs:80` builds the model in `ApiMode::ToolCalls` | yes |
| 2 | roles quoted the marker but never ran it | 29/38 quote; 0/4 recordings run it | 29/38 quote; **0** of 59/122/108/172 recorded `bash` calls (nor any `actions` entry) mentions the marker | yes |
| 3 | substitution reaches every delivered prompt | one path | all five delivered role prompts call `render_prompt_with_budget_and_shell` → `render_prompt_for_shell`; that is the only substitution site, and the three `.md` files are the only carriers of the placeholder | yes |
| 3 | validation not weakened | parser, template, limit, guard, fail-fast untouched; mini crate untouched | diff vs `9d3f488` touches only the 6 files; mini crate is its own git repo, clean at `c39b0c7`; a no-tool-call reply is still refused | yes |
| 4 | new tests red then green | exit 101 with 2 failures, then exit 0 with 7 passed | assertions are literally at `tests/prompt_shell_contract.rs:464` and `:484`; against the pre-change prompts from `9d3f488` none of the three contains "at least one tool call" and none contains any fenced or inline `echo …MARKER`; the same file runs green in my gate | yes (red is historical) |
| 4 | test exercises a real environment, not a stub | real `LocalEnvironment`, `InterruptKind::Submitted` | `mini_swe_agent::{Action, Environment, LocalEnvironment}`; `.execute(...)` must return `AgentError::Interrupt` with `InterruptKind::Submitted`; the mechanism test keeps the `echo submit` control | yes |
| 5 | retry turns and their prompt tokens | 20/10/8/0; 876,566 / 1,486,702 / 416,910; 34.45/11.65/8.12 % | same, to the token; retry call numbers `[25,27,…]` etc. reproduce exactly | yes |
| 5 | recorded totals | 2,544,563 / 12,765,478 / 5,137,090 / 3,537,843 over 69/125/102/150 calls | same; parsed/rejected split is 49+20, 115+10, 94+8, 150+0 | yes |
| 5 | after column is **projected** | labelled projected | labelled projected; no live call exists anywhere in this batch | yes |
| 5 | "the rejected turn is not saved, only the cascade" | correct | the trajectory keeps only the FormatError user message at each rejection (the prose lives under its `extra.response`), so the turn's own tokens stay spent and move to the legal completion turn; only the FormatError message and its re-sends stop | yes |
| 5 | cascade | 889,649 / 1,494,510 / 428,655 (projected) | not reproducible exactly — my (role, content, tool_calls, tool_call_id) compact-JSON ratio is 0.202727/0.173973/0.210370/0.264771, not the stated 0.259864/0.256903/0.262988/0.338006 (defect D5); order of magnitude consistent | partly |
| 5 | tail beyond the first rejected turn | 1,964,960 / 9,812,332 / 4,059,147; first rejections at 25/58/30 | reproduced to the token: 876,566+1,088,394; 1,486,702+8,325,630; 416,910+3,642,237 | yes |
| 5 | independent cross-check | "floor if the rejected calls were simply not sent" 1,667,997 / 11,278,776 / 4,720,180 / 3,537,843 | my assistant-only sums are exactly those four numbers | yes |
| 6 | gate | literal 0; 802/0/6/808; fmt 0; 0 warnings | literal 0; 802 passed / 0 failed / 6 ignored / 808 per-test lines / 60 result lines / **0** warning lines; `--list` 808; `--list --ignored` 6; `fmt --all --check` exit 0, 0 bytes | yes |
| 6 | baseline / delta | 800/0/6/806 → +2 tests | delta is exactly the two new tests; nothing removed | yes |

### Counts I can put beside the report's, side by side

| figure | report | mine |
|---|---|---|
| retry turns, iter 1 / 2 / 3 / live | 20 / 10 / 8 / 0 | 20 / 10 / 8 / 0 |
| retry prompt tokens | 876,566 / 1,486,702 / 416,910 / 0 | 876,566 / 1,486,702 / 416,910 / 0 |
| first rejected call | 25 / 58 / 30 / — | 25 / 58 / 30 / — |
| tokens in calls from the first rejection on | 1,964,960 / 9,812,332 / 4,059,147 / 0 | 1,964,960 / 9,812,332 / 4,059,147 / 0 |
| marker-quoting rejected turns | 29 | 29 |
| rejected turns without the marker | 9 | 9 |
| marker-mentioning shell commands in all four recordings | 0 | 0 |
| recorded calls / prompt tokens | 69/125/102/150 and 2,544,563/12,765,478/5,137,090/3,537,843 | identical |
| passed / failed / ignored / listed | 802 / 0 / 6 / 808 | 802 / 0 / 6 / 808 |
| warnings / fmt exit | 0 / 0 | 0 / 0 |
| tests added, removed | +2, 0 | +2, 0 |

## 2. What the measurement actually says, and which way it errs

The measured half is real and exactly as reported: 38 rejected turns costing
876,566 / 1,486,702 / 416,910 prompt tokens, 34.45 % / 11.65 % / 8.12 % of their recordings. What the
fix removes is not the rejected turn (it becomes the legal completion turn) but the `FormatError`
history message and every later re-send of it — the report's 889,649 / 1,494,510 / 428,655, which is
the only part of the "after" column that is a projection at all.

The report's "large unmeasured term" is the number a human will act on, and I checked it two ways.
First, the arithmetic is *right*: calls 25..69 / 58..125 / 30..102 are 1,964,960 / 9,812,332 /
4,059,147 prompt tokens, and dropping the rejected messages gives the four floor figures exactly.
Second, the direction of the error is **conservative, not aggressive**: the batch never reads its
largest figure as a saving it has won — it says the number needs a live call and that the risk is an
*earlier* Developer exit with a weaker artifact. Two qualifications the report does not make, both of
which reduce the figure rather than inflate it:

* Calls 25..69 are not all retry-shaped work. The gap of 1,088,394 successful tokens at the first
  rejection includes ordinary builds, tests and writes that a live role would still have to pay for
  somewhere; only the portion the role would have deferred until after its first "I am done" is
  avoided.
* An early end can itself cost a call: if the launchable gate fails on a valid-but-unfinished
  artifact, `run_loop.rs:1970-2079` starts exactly one targeted repair — a further Developer call
  that is **not** in the recorded tail.

So: the artefact does not overstate it. If anything it understates how confident the number is (it is
measurable, not merely directional) while correctly declining to claim it as a saving. No human acting
on this should expect 1,964,960 / 9,812,332 / 4,059,147 as an expected saving; expect the floor
(1,667,997 / 11,278,776 / 4,720,180) to be the *no-retries-at-all* level, and treat the difference as
the ceiling of what the fix can win.

## 3. Can this end Developer calls earlier with weaker artifacts?

Yes, and it is the change's real risk, not a hypothetical one.

* The old prompt already told the role to decide when it was finished; the recordings show it deciding
  at call 25 / 58 / 30 of 69 / 125 / 102 with prose that says "Iteration 1 complete", "Everything is
  verified. Final state:", "I'm done." The old text gave that decision **no executable form**, so the
  reply was rejected and the call continued by accident. The fix removes that brake: the same decision
  now ends the call.
* The Developer has no submitted artifact, so "is the project usable?" is
  `adapter::developer_artifact_valid` → `developer_artifact_defects` (`adapter/bevy/project.rs:469-508`),
  which checks the frozen crate name, the manifest, the lockfile and the frozen contract paths. It
  says nothing about whether the iteration's plan was implemented. `Submitted` is not a failure status
  (`runtime/write_failure.rs:44-54`), and the Developer wrap-up retry fires only on a limits-exceeded
  exit with an invalid artifact (`run_loop.rs:1735`). The only thing standing between an early,
  valid-but-unfinished artifact and the next iteration is the launchable gate and the battery, plus the
  Tester.
* A live round must therefore read, in order: (a) the call count and prompt tokens against the
  69 / 125 / 102 / 150 baselines; (b) whether `exit_status` is `Submitted` and whether it happens at
  the first self-declared finish; (c) `artifact_valid` at that moment; and — the observable the report
  does not name — (d) whether the **first** battery pass is launchable, i.e. whether the one targeted
  repair at `run_loop.rs:1970-2079` was consumed. A weaker artifact shows up there as a repair call,
  which is also the mechanism by which an early end stops saving money.

## 4. Defects found (none blocking, none a weakened check)

| id | severity | what | reproduction |
|---|---|---|---|
| D1 | low | The method sentence "a model call is one such message (assistant = parsed, user/FormatError = rejected)" plus "reproduces `hoh.usage` exactly" reads as if the recorded totals were the parsed calls'. They are not: `extract_usage` counts the rejected messages too. Read the other way the retry share would look like 52.5 % / 13.2 % / 8.8 % | assistant-only sums are 1,667,997 / 11,278,776 / 4,720,180 / 3,537,843 — the report's own floor figures |
| D2 | low | The tail is called "unmeasured" and "a direction I cannot quantify offline"; it is arithmetic over recorded usage and reproduces to the token. Only its behavioural realisation is unmeasured | sum `usage.prompt_tokens` over calls at or after the first rejection |
| D3 | informational | `tool_calls` is the **absent key**, not an explicit `null`, in all 38 rejections | JSON key census over the 38 FormatError responses |
| D4 | informational | `distinct_shapes_found: 1` whereas the batch's own table gives 29 with the marker and 9 without — two content variants, both addressed | same census |
| D5 | low | The cascade figures are given as "projected at each recording's own tokens-per-wire-byte ratio", but that ratio is not reproducible from the message schema (`0.202727/0.173973/0.210370/0.264771` from `(role, content, tool_calls, tool_call_id)` vs the stated `0.259864/0.256903/0.262988/0.338006`). The cascade is modelled either way and its magnitude is consistent with the measured retry byte share | per-call wire-byte reconstruction |

## 5. What I could not establish

* That a live Developer now runs `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` instead of writing the
  marker. No round and no model call were run, by instruction; this is the whole unmeasured half.
* The historical red run. The current tree already contains the fixed prompts, so exit code 101 and the
  two panic texts can only be checked against the prompts exported from `9d3f488` — where both
  assertions genuinely fail — not re-observed.
* The exact byte model behind the cascade figures (D5).
* Whether the Planner and the Tester retried the same way. Only Developer trajectories are in the
  corpus; the report states this limitation itself.

## 6. Gate transcript (my run)

| check | command | literal exit code | result |
|---|---|---|---|
| gate | `cargo test --offline` | **0** | 802 passed / 0 failed / 6 ignored / 808 per-test lines / 60 `test result` lines / 0 compiler warnings / 0 error lines |
| list | `cargo test --offline -- --list` | **0** | 808 test lines |
| list ignored | `cargo test --offline -- --list --ignored` | **0** | 6 test lines |
| fmt | `cargo fmt --all --check` | **0** | 0 bytes of output |

Build directory `D:/retry-acc-target`, this pass's own; `F:` was checked first (9.1 G free, 100 % used)
and the build was put on `D:` (72 G free). One test process at a time. No `rm -rf`, no wildcard, no
`git checkout --`.
